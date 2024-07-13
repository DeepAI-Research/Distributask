import os
import json
import time
import requests
from tqdm import tqdm
from typing import Dict, List
import atexit
import tempfile

from celery import Celery
from redis import ConnectionPool, Redis
from omegaconf import OmegaConf
from dotenv import load_dotenv
from huggingface_hub import HfApi, Repository
from requests.exceptions import HTTPError
from celery.utils.log import get_task_logger


class Distributask:
    """
    The Distributask class contains the core features of distributask, including creating and
    executing the task queue, managing workers using the Vast.ai API, and uploading files and directories
    using the Hugging Face API.
    """

    app: Celery = None
    redis_client: Redis = None
    registered_functions: dict = {}
    pool: ConnectionPool = None

    def __init__(
        self,
        hf_repo_id=os.getenv("HF_REPO_ID"),
        hf_token=os.getenv("HF_TOKEN"),
        vast_api_key=os.getenv("VAST_API_KEY"),
        redis_host=os.getenv("REDIS_HOST", "localhost"),
        redis_password=os.getenv("REDIS_PASSWORD", ""),
        redis_port=os.getenv("REDIS_PORT", 6379),
        redis_username=os.getenv("REDIS_USER", "default"),
        broker_pool_limit=os.getenv("BROKER_POOL_LIMIT", 1),
    ) -> None:
        """
        Initialize the Distributask object with the provided configuration parameters. Also sets some
        default settings in Celery and handles cleanup of Celery queue and Redis server on exit.

        Args:
            hf_repo_id (str): Hugging Face repository ID.
            hf_token (str): Hugging Face API token.
            vast_api_key (str): Vast.ai API key.
            redis_host (str): Redis host. Defaults to "localhost".
            redis_password (str): Redis password. Defaults to an empty string.
            redis_port (int): Redis port. Defaults to 6379.
            redis_username (str): Redis username. Defaults to "default".
            broker_pool_limit (int): Celery broker pool limit. Defaults to 1.

        Raises:
            ValueError: If any of the required parameters (hf_repo_id, hf_token, vast_api_key) are not provided.
        """
        if hf_repo_id is None:
            raise ValueError(
                "HF_REPO_ID is not provided to the Distributask constructor"
            )

        if hf_token is None:
            raise ValueError("HF_TOKEN is not provided to the Distributask constructor")

        if vast_api_key is None:
            raise ValueError(
                "VAST_API_KEY is not provided to the Distributask constructor"
            )

        if redis_host == "localhost":
            print(
                "WARNING: Using default Redis host 'localhost'. This is not recommended for production use and won't work for distributed rendering."
            )

        self.settings = {
            "HF_REPO_ID": hf_repo_id,
            "HF_TOKEN": hf_token,
            "VAST_API_KEY": vast_api_key,
            "REDIS_HOST": redis_host,
            "REDIS_PASSWORD": redis_password,
            "REDIS_PORT": redis_port,
            "REDIS_USER": redis_username,
            "BROKER_POOL_LIMIT": broker_pool_limit,
        }

        redis_url = self.get_redis_url()
        # start Celery app instance
        self.app = Celery("distributask", broker=redis_url, backend=redis_url)
        self.app.conf.broker_pool_limit = self.settings["BROKER_POOL_LIMIT"]

        def cleanup_redis():
            """
            Deletes keys in redis related to Celery tasks and closes the Redis connection on exit
            """
            patterns = ["celery-task*", "task_status*"]
            redis_connection = self.get_redis_connection()
            for pattern in patterns:
                for key in redis_connection.scan_iter(match=pattern):
                    redis_connection.delete(key)
            print("Redis server cleared")

        def cleanup_celery():
            """
            Clears Celery task queue on exit
            """
            self.app.control.purge()
            print("Celery queue cleared")

        # At exit, close Celery instance, delete all previous task info from queue and Redis, and close Redis
        atexit.register(self.app.close)
        atexit.register(cleanup_redis)
        atexit.register(cleanup_celery)

        self.redis_client = self.get_redis_connection()

        # Tasks are acknowledged after they have been executed
        self.app.conf.task_acks_late = True
        self.call_function_task = self.app.task(
            bind=True, name="call_function_task", max_retries=3, default_retry_delay=30
        )(self.call_function_task)

    def __del__(self):
        """Destructor to clean up resources."""
        if self.pool is not None:
            self.pool.disconnect()
        if self.redis_client is not None:
            self.redis_client.close()
        if self.app is not None:
            self.app.close()

    def log(self, message: str, level: str = "info") -> None:
        """
        Log a message with the specified level.

        Args:
            message (str): The message to log.
            level (str): The logging level. Defaults to "info".
        """
        logger = get_task_logger(__name__)
        getattr(logger, level)(message)

    def get_settings(self) -> str:
        """
        Return settings of distributask instance.
        """
        return self.settings

    def get_redis_url(self) -> str:
        """
        Construct a Redis URL from the configuration settings.

        Returns:
            str: A Redis URL string.

        Raises:
            ValueError: If any required Redis connection parameter is missing.
        """
        host = self.settings["REDIS_HOST"]
        password = self.settings["REDIS_PASSWORD"]
        port = self.settings["REDIS_PORT"]
        username = self.settings["REDIS_USER"]

        if None in [host, password, port, username]:
            raise ValueError("Missing required Redis configuration values")

        redis_url = f"redis://{username}:{password}@{host}:{port}"
        return redis_url

    def get_redis_connection(self, force_new: bool = False) -> Redis:
        """
        Returns Redis connection. If it already exists, returns current connection.
        If it does not exist, its create a new Redis connection using a connection pool.

        Args:
            force_new (bool): Force the creation of a new connection if set to True. Defaults to False.

        Returns:
            Redis: A Redis connection object.
        """
        if self.redis_client is not None and not force_new:
            return self.redis_client
        else:
            self.pool = ConnectionPool(host=self.settings["REDIS_HOST"], 
                                       port=self.settings["REDIS_PORT"],
                                       password=self.settings["REDIS_PASSWORD"], 
                                       max_connections=1)
            self.redis_client = Redis(connection_pool=self.pool)
            atexit.register(self.pool.disconnect)

        return self.redis_client

    def get_env(self, key: str, default: any = None) -> any:
        """
        Retrieve a value from the configuration or .env file, with an optional default if the key is not found.

        Args:
            key (str): The key to look for in the settings.
            default (any): The default value to return if the key is not found. Defaults to None.

        Returns:
            any: The value from the settings if the key exists, otherwise the default value.
        """
        return self.settings.get(key, default)

    def call_function_task(self, func_name: str, args_json: str) -> any:
        """
        Creates Celery task that executes a registered function with provided JSON arguments.

        Args:
            func_name (str): The name of the registered function to execute.
            args_json (str): JSON string representation of the arguments for the function.

        Returns:
            any: Celery.app.task object, represents result of the registered function

        Raises:
            ValueError: If the function name is not registered.
            Exception: If an error occurs during the execution of the function. The task will retry in this case.
        """
        try:
            if func_name not in self.registered_functions:
                raise ValueError(f"Function '{func_name}' is not registered.")

            func = self.registered_functions[func_name]
            args = json.loads(args_json)
            result = func(**args)
            self.update_function_status(self.call_function_task.request.id, "success")

            return result
        except Exception as e:
            self.log(f"Error in call_function_task: {str(e)}", "error")
            self.call_function_task.retry(exc=e)

        return result

    def register_function(self, func: callable) -> callable:
        """
        Decorator to register a function so that it can be invoked as a Celery task.

        Args:
            func (callable): The function to register.

        Returns:
            callable: The original function, now registered as a callable task.
        """
        self.registered_functions[func.__name__] = func
        return func

    def execute_function(self, func_name: str, args: dict) -> Celery.AsyncResult:
        """
        Execute a registered function as a Celery task with provided arguments.

        Args:
            func_name (str): The name of the function to execute.
            args (dict): Arguments to pass to the function.

        Returns:
            celery.result.AsyncResult: An object representing the asynchronous result of the task.
        """
        args_json = json.dumps(args)
        async_result = self.call_function_task.delay(func_name, args_json)
        return async_result

    def update_function_status(self, task_id: str, status: str) -> None:
        """
        Update the status of a function task as a new Redis key.

        Args:
            task_id (str): The ID of the task.
            status (str): The new status to set.
        """
        redis_client = self.get_redis_connection()
        redis_client.set(f"task_status:{task_id}", status)

    def initialize_dataset(self, **kwargs) -> None:
        """
        Initialize a Hugging Face repository if it doesn't exist. Reads Hugging Face info from config or .env

        Args:
            kwargs: kwargs that can be passed into the HfApi.create_repo function.

        Raises:
            HTTPError: If repo cannot be created due to connection error other than repo not existing
        """
        repo_id = self.settings.get("HF_REPO_ID")
        hf_token = self.settings.get("HF_TOKEN")
        api = HfApi(token=hf_token)

        # creates new repo if desired repo is not found
        try:
            repo_info = api.repo_info(repo_id=repo_id, repo_type="dataset", timeout=30)
        except HTTPError as e:
            if e.response.status_code == 404:
                self.log(
                    f"Repository {repo_id} does not exist. Creating a new repository.",
                    "warn",
                )
                api.create_repo(
                    repo_id=repo_id, token=hf_token, repo_type="dataset", **kwargs
                )
            else:
                raise e

        # Create config.json file
        config = {
            "data_loader_name": "custom",
            "data_loader_kwargs": {
                "path": repo_id,
                "format": "files",
                "fields": ["file_path", "text"],
            },
        }

        # apply config.json to created repo
        with tempfile.TemporaryDirectory() as temp_dir:
            with Repository(
                local_dir=temp_dir,
                clone_from=repo_id,
                repo_type="dataset",
                use_auth_token=hf_token,
            ).commit(commit_message="Add config.json"):
                with open(os.path.join(temp_dir, "config.json"), "w") as f:
                    json.dump(config, f, indent=2)

        self.log(f"Initialized repository {repo_id}.")

    # upload a single file to the Hugging Face repository
    def upload_file(self, file_path: str) -> None:
        """
        Upload a file to a Hugging Face repository.

        Args:
            file_path (str): The path of the file to upload.

        Raises:
            Exception: If an error occurs during the upload process.

        """
        hf_token = self.settings.get("HF_TOKEN")
        repo_id = self.settings.get("HF_REPO_ID")

        api = HfApi(token=hf_token)

        try:
            self.log(f"Uploading {file_path} to Hugging Face repo {repo_id}")
            api.upload_file(
                path_or_fileobj=file_path,
                path_in_repo=os.path.basename(file_path),
                repo_id=repo_id,
                token=hf_token,
                repo_type="dataset",
            )
            self.log(f"Uploaded {file_path} to Hugging Face repo {repo_id}")
        except Exception as e:
            self.log(
                f"Failed to upload {file_path} to Hugging Face repo {repo_id}: {e}",
                "error",
            )

    def upload_directory(self, dir_path: str) -> None:
        """
        Upload a directory to a Hugging Face repository. Can be used to reduce frequency of Hugging Face API
        calls if you are rate limited while using the upload_file function.

        Args:
            dir_path (str): The path of the directory to upload.

        Raises:
            Exception: If an error occurs during the upload process.

        """
        hf_token = self.settings.get("HF_TOKEN")
        repo_id = self.settings.get("HF_REPO_ID")

        try:
            self.log(f"Uploading {dir_path} to Hugging Face repo {repo_id}")

            api = HfApi(token=hf_token)
            api.upload_folder(
                folder_path=dir_path,
                repo_id=repo_id,
                repo_type="dataset",
            )
            self.log(f"Uploaded {dir_path} to Hugging Face repo {repo_id}")
        except Exception as e:
            self.log(
                f"Failed to upload {dir_path} to Hugging Face repo {repo_id}: {e}",
                "error",
            )

    def delete_file(self, repo_id: str, path_in_repo: str) -> None:
        """
        Delete a file from a Hugging Face repository.

        Args:
            repo_id (str): The ID of the repository.
            path_in_repo (str): The path of the file to delete within the repository.

        Raises:
            Exception: If an error occurs during the deletion process.

        """
        hf_token = self.settings.get("HF_TOKEN")
        api = HfApi(token=hf_token)

        try:
            api.delete_file(
                repo_id=repo_id,
                path_in_repo=path_in_repo,
                repo_type="dataset",
                token=hf_token,
            )
            self.log(f"Deleted {path_in_repo} from Hugging Face repo {repo_id}")
        except Exception as e:
            self.log(
                f"Failed to delete {path_in_repo} from Hugging Face repo {repo_id}: {e}",
                "error",
            )

    def file_exists(self, repo_id: str, path_in_repo: str) -> bool:
        """
        Check if a file exists in a Hugging Face repository.

        Args:
            repo_id (str): The ID of the repository.
            path_in_repo (str): The path of the file to check within the repository.

        Returns:
            bool: True if the file exists in the repository, False otherwise.

        Raises:
            Exception: If an error occurs while checking the existence of the file.
        """
        hf_token = self.settings.get("HF_TOKEN")
        api = HfApi(token=hf_token)

        try:
            repo_files = api.list_repo_files(
                repo_id=repo_id, repo_type="dataset", token=hf_token
            )
            return path_in_repo in repo_files
        except Exception as e:
            self.log(
                f"Failed to check if {path_in_repo} exists in Hugging Face repo {repo_id}: {e}",
                "error",
            )
            return False

    def list_files(self, repo_id: str) -> list:
        """
        Get a list of files from a Hugging Face repository.

        Args:
            repo_id (str): The ID of the repository.

        Returns:
            list: A list of file paths in the repository.

        Raises:
            Exception: If an error occurs while retrieving the list of files.
        """
        hf_token = self.settings.get("HF_TOKEN")
        api = HfApi(token=hf_token)

        try:
            repo_files = api.list_repo_files(
                repo_id=repo_id, repo_type="dataset", token=hf_token
            )
            return repo_files
        except Exception as e:
            self.log(
                f"Failed to get the list of files from Hugging Face repo {repo_id}: {e}",
                "error",
            )
            return []

    def search_offers(self, max_price: float) -> List[Dict]:
        """
        Search for available offers to rent a node as an instance on the Vast.ai platform.

        Args:
            max_price (float): The maximum price per hour for the instance.

        Returns:
            List[Dict]: A list of dictionaries representing the available offers.

        Raises:
            requests.exceptions.RequestException: If there is an error while making the API request.
        """
        api_key = self.get_env("VAST_API_KEY")
        base_url = "https://console.vast.ai/api/v0/bundles/"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        url = (
            base_url
            + '?q={"gpu_ram":">=4","rentable":{"eq":true},"dph_total":{"lte":'
            + str(max_price)
            + '},"sort_option":{"0":["dph_total","asc"],"1":["total_flops","asc"]}}'
        )

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            json_response = response.json()
            return json_response["offers"]

        except requests.exceptions.RequestException as e:
            self.log(
                f"Error: {e}\nResponse: {response.text if response else 'No response'}"
            )
            raise

    def create_instance(
        self, offer_id: str, image: str, module_name: str, env_settings: Dict, command: str
    ) -> Dict:
        """
        Create an instance on the Vast.ai platform.

        Args:
            offer_id (str): The ID of the offer to create the instance from.
            image (str): The image to use for the instance. (example: RaccoonResearch/distributask-test-worker)
            module_name (str): The name of the module to run on the instance, configured to be a docker file (example: distributask.example.worker)
            command (str): command that initializes celery worker. Has default command if not passed in.

        Returns:
            Dict: A dictionary representing the created instance.

        Raises:
            ValueError: If the Vast.ai API key is not set in the environment.
            Exception: If there is an error while creating the instance.
        """
        if self.get_env("VAST_API_KEY") is None:
            self.log("VAST_API_KEY is not set in the environment", "error")
            raise ValueError("VAST_API_KEY is not set in the environment")

        if command is None:
            command = f"celery -A {module_name} worker --loglevel=info --concurrency=1 --without-heartbeat --prefetch_multiplier=1"

        if env_settings is None:
            env_settings = self.settings

        json_blob = {
            "client_id": "me",
            "image": image,
            "env": env_settings,
            "disk": 32,  # Set a non-zero value for disk
            "onstart": f"export PATH=$PATH:/ && cd ../ && {command}",
            "runtype": "ssh ssh_proxy",
        }
        url = f"https://console.vast.ai/api/v0/asks/{offer_id}/?api_key={self.get_env('VAST_API_KEY')}"
        headers = {"Authorization": f"Bearer {self.get_env('VAST_API_KEY')}"}
        response = requests.put(url, headers=headers, json=json_blob)

        if response.status_code != 200:
            self.log(f"Failed to create instance: {response.text}", "error")
            raise Exception(f"Failed to create instance: {response.text}")

        return response.json()

    def destroy_instance(self, instance_id: str) -> Dict:
        """
        Destroy an instance on the Vast.ai platform.

        Args:
            instance_id (str): The ID of the instance to destroy.

        Returns:
            Dict: A dictionary representing the result of the destroy operation.
        """
        api_key = self.get_env("VAST_API_KEY")
        headers = {"Authorization": f"Bearer {api_key}"}
        url = (
            f"https://console.vast.ai/api/v0/instances/{instance_id}/?api_key={api_key}"
        )
        response = requests.delete(url, headers=headers)
        return response.json()

    def rent_nodes(
        self,
        max_price: float,
        max_nodes: int,
        image: str,
        module_name: str,
        env_settings: Dict = None,
        command: str = None,
    ) -> List[Dict]:
        """
        Rent nodes as an instance on the Vast.ai platform.

        Args:
            max_price (float): The maximum price per hour for the nodes.
            max_nodes (int): The maximum number of nodes to rent.
            image (str): The image to use for the nodes.
            module_name (str): The name of the module to run on the nodes.

        Returns:
            List[Dict]: A list of dictionaries representing the rented nodes. If error is encountered
            trying to rent, it will retry every 5 seconds.
        """
        rented_nodes: List[Dict] = []
        while len(rented_nodes) < max_nodes:
            search_retries = 10
            while search_retries > 0:
                try:
                    offers = self.search_offers(max_price)
                    break
                except Exception as e:
                    self.log(
                        f"Error searching for offers: {str(e)} - retrying in 5 seconds...",
                        "error",
                    )
                    search_retries -= 1
                    # sleep for 5 seconds before retrying
                    time.sleep(5)
                    continue

            offers = sorted(
                offers, key=lambda offer: offer["dph_total"]
            )  # Sort offers by price, lowest to highest
            for offer in offers:
                if len(rented_nodes) >= max_nodes:
                    break
                try:
                    instance = self.create_instance(
                        offer["id"], image, module_name, env_settings=env_settings, command=command
                    )
                    atexit.register(self.destroy_instance, instance["new_contract"])
                    rented_nodes.append(
                        {
                            "offer_id": offer["id"],
                            "instance_id": instance["new_contract"],
                        }
                    )
                except Exception as e:
                    self.log(
                        f"Error renting node: {str(e)} - searching for new offers",
                        "error",
                    )
                    break  # Break out of the current offer iteration
            else:
                # If the loop completes without breaking, all offers have been tried
                self.log("No more offers available - stopping node rental", "warning")
                break
        return rented_nodes

    def get_node_log(self, node: Dict, wait_time: int = 2):
        """
        Get the log of the Vast.ai instance that is passed in. Makes an api call to tell the instance to send the log,
        and another one to actually retrive the log
        Args:
            node (Dict): the node that corresponds to the Vast.ai instance you want the log from
            wait_time (int): how long to wait in between the two api calls described above

        Returns:
            str: the log of the instance requested. If anything else other than a code 200 is received, return None
        """
        node_id = node["instance_id"]
        url = f"https://console.vast.ai/api/v0/instances/request_logs/{node_id}/"

        payload = {"tail": "1000"}
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.settings['VAST_API_KEY']}",
        }

        response = requests.request(
            "PUT", url, headers=headers, json=payload, timeout=5
        )

        if response.status_code == 200:
            log_url = response.json()["result_url"]
            time.sleep(wait_time)
            log_response = requests.get(log_url, timeout=5)
            if log_response.status_code == 200:
                return log_response
            else:
                return None
        else:
            return None

    def terminate_nodes(self, nodes: List[Dict]) -> None:
        """
        Terminate the instances of rented nodes on Vast.ai.

        Args:
            nodes (List[Dict]): A list of dictionaries representing the rented nodes.

        Raises:
            Exception: If error in destroying instances.
        """
        for node in nodes:
            try:
                self.destroy_instance(node["instance_id"])
            except Exception as e:
                self.log(
                    f"Error terminating node: {node['instance_id']}, {str(e)}", "error"
                )

    def monitor_tasks(
        self, tasks, update_interval=1, show_time_left=True, print_statements=True
    ):
        """
        Monitor the status of the tasks on the Vast.ai nodes.

        Args:
            tasks (List): A list of the tasks to monitor. Should be a list of the results of execute_function.
            update_interval (bool): Number of seconds the status of tasks are updated.
            show_time_left (bool): Show the estimated time left to complete tasks using the tqdm progress bar
            print_statments (bool): Allow printing of status of task queue

        Raises:
            Exception: If error in the process of executing the tasks
        """

        try:
            # Wait for the tasks to complete
            if print_statements:
                print("Tasks submitted to queue. Starting queue...")
                print("Elapsed time<Estimated time to completion")
            with tqdm(total=len(tasks), unit="task") as pbar:
                while not all(task.ready() for task in tasks):
                    current_tasks = sum([task.ready() for task in tasks])
                    pbar.update(current_tasks - pbar.n)
                    time.sleep(update_interval)
        except Exception as e:
            self.log(f"Error in executing tasks on nodes, {str(e)}")

        if all(task.ready() for task in tasks):
            print("All tasks completed.")


distributask = None


def create_from_config(config_path="config.json", env_path=".env") -> Distributask:
    """
    Create Distributask object using settings that merge config.json and .env files present in distributask directory.
    If there are conflicting values, the .env takes priority.

    Args:
        config_path (str): path to config.json file
        env_path (str): path to .env file

    Returns:
        Distributask object initialized with settings from config or .env file
    """
    print("**** CREATE_FROM_CONFIG ****")
    global distributask
    if distributask is not None:
        return distributask
    # Load environment variables from .env file
    try:
        load_dotenv(env_path)
    except:
        print("No .env file found. Using system environment variables only.")

    # Load configuration from JSON file
    try:
        settings = OmegaConf.load(config_path)
        if not all(settings.values()):
            print(f"Configuration file is missing necessary values.")
    except:
        print(
            "Configuration file not found. Falling back to system environment variables."
        )
        settings = {}

    env_dict = {key: value for key, value in os.environ.items()}
    settings = OmegaConf.merge(settings, OmegaConf.create(env_dict))

    distributask = Distributask(
        hf_repo_id=settings.get("HF_REPO_ID"),
        hf_token=settings.get("HF_TOKEN"),
        vast_api_key=settings.get("VAST_API_KEY"),
        redis_host=settings.get("REDIS_HOST"),
        redis_password=settings.get("REDIS_PASSWORD"),
        redis_port=settings.get("REDIS_PORT"),
        redis_username=settings.get("REDIS_USER"),
        broker_pool_limit=int(settings.get("BROKER_POOL_LIMIT", 1)),
    )

    return distributask
