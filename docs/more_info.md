# Summary of useful functions

#### Settings, Environment, and Help

- `create_from_config()` - creates Distribtaur instance using environment variables
- `get_env(key)` - gets value from .env
- `get_settings(key)` - gets value from settings dictionary

#### Celery tasks

- `register_function(func)` - registers function to be task for worker
- `execute_function(func_name, args)` - creates Celery task using registered function

#### Redis server

- `get_redis_url()` - gets Redis host url 
- `get_redis_connection()` - gets Redis connection instance
 
#### Worker management via Vast.ai API

- `search_offers(max_price)` - searches for available instances on Vast.ai
- `rent_nodes(max_price, max_nodes, image, module_name, command)` - rents nodes using Vast.ai instance
- `terminate_nodes(node_id_lists)` - terminates Vast.ai instance


#### HuggingFace repositories and uploading

- `initialize_dataset()` - intializes dataset repo on HuggingFace
- `upload_file(path_to_file)` - uploads file to Huggingface
- `upload_directory(path_to_directory)` - uploads folder to Huggingface repo
- `delete_file(path_to_file)` - deletes file on HuggingFace repo

#### Visit the [Distributaur Class](distributaur.md) page for full, detailed documentation of the distributaur class.

# Initialized Settings

The Distributaur class is initialized with various settings. The ones that depend on the environment are taken from a .env or config.json file present in the parent directory. The following are other settings that deal directory with the Celery app or features for your convience of use:


#### Tasks are acknowledged after they are executed

`celery.app.tasks_acks_late = 1`

#### Worker only fetches one task at a time

`celery.app.worker_prefetch_multiplier = 1`

#### If task creation fails, retry 3 times, waiting 30 seconds between each retry

`celery.app.task.max_retries = 3`
`celery.app.default_retry_delay = 30`

# Docker Setup

Distributaur uses a Docker image to transfer the environment and files to the Vast.ai nodes. In your implementation using distributaur, you can use the Docker file in the distributaur repository as a base for your own Docker file. If you choose to do this, be sure to add requirements.txt (and add distributaur to the list of packages) to your directory as well so the Docker image has the required packages.

# Important Packages

Visit the websites of these wonderful packages to learn more about how they work and how to use them.

Celery: `https://docs.celeryq.dev/en/stable/`   
Redis: `https://redis.io/docs/latest/`  
Hugging Face: `https://huggingface.co/docs/huggingface_hub/en/guides/upload` 