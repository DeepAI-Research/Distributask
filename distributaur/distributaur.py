import os
import sys
import json
import requests
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

import atexit
from subprocess import Popen
import sys


class Distributaur:
    """
    Configuration management class that stores settings and provides methods to update and retrieve these settings.
    """

    app: Celery = None
    redis_client: Redis = None
    registered_functions: dict = {}
    pool: ConnectionPool = None

    flower_processes = []

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
        Initialize the Distributaur object with the provided configuration parameters.

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
                "HF_REPO_ID is not provided to the Distributaur constructor"
            )

        if hf_token is None:
            raise ValueError("HF_TOKEN is not provided to the Distributaur constructor")

        if vast_api_key is None:
            raise ValueError(
                "VAST_API_KEY is not provided to the Distributaur constructor"
            )

        if redis_host == "localhost":
            print(
                "WARNING: Using default Redis host 'localhost'. This is not recommended for production use and won't work for distributed rendering."
            )

        self.settings = {
            "HF_REPO_ID": hf_repo_id,
            "HF_TOKEN": hf_token,
            "VAST_API_KEY": vast_api_key,
            "redis": {
                "host": redis_host,
                "password": redis_password,
                "port": redis_port,
                "username": redis_username,
                "broker_pool_limit": broker_pool_limit,
            },
        }

        redis_url = self.get_redis_url()
        self.app = Celery("distributaur", broker=redis_url, backend=redis_url)
        self.app.conf.broker_pool_limit = self.settings["redis"]["broker_pool_limit"]

        # At exit, close app
        atexit.register(self.app.close)

        def close_flower_processes():
            for process in self.flower_processes:
                process.terminate()
            self.flower_processes.clear()

        atexit.register(close_flower_processes)

        self.app.task_acks_late = True
        self.app.worker_prefetch_multiplier = 1
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

    def get_redis_url(self) -> str:
        """
        Construct a Redis URL from the configuration settings.

        Returns:
            str: A Redis URL string built from the configuration settings.

        Raises:
            ValueError: If any required Redis connection parameter is missing.
        """
        redis_config = self.settings["redis"]
        host = redis_config["host"]
        password = redis_config["password"]
        port = redis_config["port"]
        username = redis_config["username"]

        if None in [host, password, port, username]:
            raise ValueError("Missing required Redis configuration values")

        redis_url = f"redis://{username}:{password}@{host}:{port}"
        return redis_url

    def get_redis_connection(self, force_new: bool = False) -> Redis:
        """
        Retrieve or create a new Redis connection using the connection pool.

        Args:
            force_new (bool): Force the creation of a new connection if set to True. Defaults to False.

        Returns:
            Redis: A Redis connection object.
        """
        if self.redis_client is not None and not force_new:
            return self.redis_client
        else:
            redis_url = self.get_redis_url()
            self.pool = ConnectionPool.from_url(redis_url)
            self.redis_client = Redis(connection_pool=self.pool)
            atexit.register(self.pool.disconnect)
            atexit.register(self.redis_client.close)

        return self.redis_client

    def get_env(self, key: str, default: any = None) -> any:
        """
        Retrieve a value from the configuration settings, with an optional default if the key is not found.

        Args:
            key (str): The key to look for in the settings.
            default (any): The default value to return if the key is not found. Defaults to None.

        Returns:
            any: The value from the settings if the key exists, otherwise the default value.
        """
        return self.settings.get(key, default)

    def call_function_task(self, func_name: str, args_json: str) -> any:
        """
        Celery task to execute a registered function with provided JSON arguments.

        Args:
            func_name (str): The name of the registered function to execute.
            args_json (str): JSON string representation of the arguments for the function.

        Returns:
            any: The result of the function execution.

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
            self.update_function_status(self.call_function_task.request.id, "completed")

            return result
        except Exception as e:
            self.log(f"Error in call_function_task: {str(e)}", "error")
            self.call_function_task.retry(exc=e)

        return result

    def register_function(self, func: callable) -> callable:
        """
        Decorator to register a function so that it can be invoked as a task.

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
        return self.call_function_task.delay(func_name, args_json)

    def update_function_status(self, task_id: str, status: str) -> None:
        """
        Update the status of a function task in Redis.

        Args:
            task_id (str): The ID of the task.
            status (str): The new status to set.
        """
        redis_client = self.get_redis_connection()
        redis_client.set(f"task_status:{task_id}", status)

    def initialize_dataset(self, **kwargs) -> None:
        """Initialize a Hugging Face repository if it doesn't exist."""
        repo_id = self.settings.get("HF_REPO_ID")
        hf_token = self.settings.get("HF_TOKEN")
        api = HfApi(token=hf_token)

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

        self.initialize_dataset()

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

    def upload_directory(self, output_dir: str, repo_dir: str) -> None:
        """
        Upload the rendered outputs to a Huggingface repository.

        Args:
            output_dir (str): The local directory containing the files to upload.
            repo_dir (str): The directory path in the repository where the files will be uploaded.

        Raises:
            Exception: If an error occurs during the upload process for any file.
        """
        hf_token = self.settings.get("HF_TOKEN")
        repo_id = self.settings.get("HF_REPO_ID")

        self.initialize_dataset()

        api = HfApi(token=hf_token)

        for root, dirs, files in os.walk(output_dir):
            for file in files:
                local_path = os.path.join(root, file)
                path_in_repo = os.path.join(repo_dir, file) if repo_dir else file

                try:
                    self.log(
                        f"Uploading {local_path} to Hugging Face repo {repo_id} at {path_in_repo}"
                    )
                    api.upload_file(
                        path_or_fileobj=local_path,
                        path_in_repo=path_in_repo,
                        repo_id=repo_id,
                        token=hf_token,
                        repo_type="dataset",
                    )
                    self.log(
                        f"Uploaded {local_path} to Hugging Face repo {repo_id} at {path_in_repo}"
                    )
                except Exception as e:
                    self.log(
                        f"Failed to upload {local_path} to Hugging Face repo {repo_id} at {path_in_repo}: {e}",
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
        Search for available offers on the Vast.ai platform.

        Args:
            max_price (float): The maximum price per hour for the offers.

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

    def create_instance(self, offer_id: str, image: str, module_name: str) -> Dict:
        """
        Create an instance on the Vast.ai platform.

        Args:
            offer_id (str): The ID of the offer to create the instance from.
            image (str): The image to use for the instance. (example: RaccoonResearch/distributaur-test-worker)
            module_name (str): The name of the module to run on the instance (example: distributaur.example.worker)

        Returns:
            Dict: A dictionary representing the created instance.

        Raises:
            ValueError: If the Vast.ai API key is not set in the environment.
            Exception: If there is an error while creating the instance.
        """
        if self.get_env("VAST_API_KEY") is None:
            self.log("VAST_API_KEY is not set in the environment", "error")
            raise ValueError("VAST_API_KEY is not set in the environment")

        json_blob = {
            "client_id": "me",
            "image": image,
            "env": "",
            "disk": 16,  # Set a non-zero value for disk
            "onstart": f"export PATH=$PATH:/ &&  cd ../ && REDIS_HOST={self.get_env('REDIS_HOST')} REDIS_PORT={self.get_env('REDIS_PORT')} REDIS_USER={self.get_env('REDIS_USER')} REDIS_PASSWORD={self.get_env('REDIS_PASSWORD')} HF_TOKEN={self.get_env('HF_TOKEN')} HF_REPO_ID={self.get_env('HF_REPO_ID')} VAST_API_KEY={self.get_env('VAST_API_KEY')} celery -A {module_name} worker --loglevel=info",
            "runtype": "ssh ssh_proxy",
            "image_login": None,
            "python_utf8": False,
            "lang_utf8": False,
            "use_jupyter_lab": False,
            "jupyter_dir": None,
            "create_from": "",
            "template_hash_id": "250671155ccbc28d0609af524b75a80e",
            "template_id": 108305,
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

    def rent_nodes(self, max_price: float, max_nodes: int, image: str, module_name: str) -> List[Dict]:
        """
        Rent nodes on the Vast.ai platform.

        Args:
            max_price (float): The maximum price per hour for the nodes.
            max_nodes (int): The maximum number of nodes to rent.
            image (str): The image to use for the nodes.

        Returns:
            List[Dict]: A list of dictionaries representing the rented nodes.
        """
        offers = self.search_offers(max_price)
        rented_nodes: List[Dict] = []
        for offer in offers:
            if len(rented_nodes) >= max_nodes:
                break
            try:
                instance = self.create_instance(offer["id"], image, module_name)
                rented_nodes.append(
                    {"offer_id": offer["id"], "instance_id": instance["new_contract"]}
                )
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [400, 404]:
                    pass
                else:
                    raise
        atexit.register(self.terminate_nodes, rented_nodes)
        return rented_nodes

    def terminate_nodes(self, nodes: List[Dict]) -> None:
        """
        Terminate the rented nodes.

        Args:
            nodes (List[Dict]): A list of dictionaries representing the rented nodes.
        """
        for node in nodes:
            try:
                self.destroy_instance(node["instance_id"])
            except Exception as e:
                self.log(
                    f"Error terminating node: {node['instance_id']}, {str(e)}", "error"
                )

    def start_monitoring_server(
        self, worker_name="distributaur.example.worker"
    ) -> None:
        """
        Start Flower monitoring in a separate process.
        The monitoring process will be automatically terminated when the main process exits.
        """
        # get the current python process
        flower_process = Popen(
            [
                sys.executable,
                "-m" "celery",
                "-A",
                worker_name,
                "flower",
            ]
        )

        self.flower_processes.append(flower_process)

    def stop_monitoring_server(self) -> None:
        """
        Stop Flower monitoring by terminating the Flower process.
        """
        for process in self.flower_processes:
            process.terminate()
        self.flower_processes.clear()


def create_from_config(config_path="config.json", env_path=".env") -> Distributaur:
    # Load environment variables from .env file
    try:
        load_dotenv(env_path)
    except:
        print("No .env file found. Using system environment variables only.")

    # Load configuration from JSON file
    try:
        settings = OmegaConf.load(config_path)
        if not all(settings.values()) or not all(
            settings.get("redis", {"host": None}).values()
        ):
            print(f"Configuration file is missing necessary values.")
    except:
        print(
            "Configuration file not found. Falling back to system environment variables."
        )
        settings = {}

    env_dict = {key: value for key, value in os.environ.items()}
    settings = OmegaConf.merge(settings, OmegaConf.create(env_dict))

    distributaur = Distributaur(
        hf_repo_id=settings.get("HF_REPO_ID"),
        hf_token=settings.get("HF_TOKEN"),
        vast_api_key=settings.get("VAST_API_KEY"),
        redis_host=settings.get("REDIS_HOST", settings.get("redis", {}).get("host")),
        redis_password=settings.get(
            "REDIS_PASSWORD", settings.get("redis", {}).get("password")
        ),
        redis_port=settings.get("REDIS_PORT", settings.get("redis", {}).get("port")),
        redis_username=settings.get(
            "REDIS_USER", settings.get("redis", {}).get("username")
        ),
        broker_pool_limit=settings.get(
            "BROKER_POOL_LIMIT", settings.get("redis", {}).get("broker_pool_limit")
        ),
    )
    return distributaur
