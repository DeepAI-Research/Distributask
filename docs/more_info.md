# Summary of useful functions

#### Settings, Environment, and Help

- `create_from_config()` - creates Distribtask instance using environment variables
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

#### Visit the [Distributask Class](distributask.md) page for full, detailed documentation of the distributask class.

# Docker Setup

Distributask uses a Docker image to transfer the environment and files to the Vast.ai nodes. In your implementation using Distributask, you can use the Docker file in the Distributask repository as a base for your own Docker file. If you choose to do this, be sure to add requirements.txt (and add distributask to the list of packages) to your directory as well so the Docker image has the required packages.

# Important Packages

Visit the websites of these wonderful packages to learn more about how they work and how to use them.

Celery: `https://docs.celeryq.dev/en/stable/`   
Redis: `https://redis.io/docs/latest/`  
Hugging Face: `https://huggingface.co/docs/huggingface_hub/en/guides/upload` 