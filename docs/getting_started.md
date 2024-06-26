# Getting Started

Below are some quick notes to get you up and running. Please read through the rest of the documentation for more detailed information.

# Installation

```bash
pip install distributaur
```

# Development

### Prerequisites

- Python 3.8 or newer (tested on 3.11)
- Redis server
- Celery

### Setup

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/RaccoonResearch/distributaur.git
cd distributaur
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Install the distributaur package:

```bash
python setup.py install
```

### Configuration

Create a `.env` file in the root directory of your project or set environment variables to match your setup:

```plaintext
REDIS_HOST=redis_host
REDIS_PORT=redis_port
REDIS_USER=redis_user
REDIS_PASSWORD=redis_password
VAST_API_KEY=your_vastai_api_key
HF_TOKEN=your_huggingface_token
HF_REPO_ID=your_huggingface_repo
BROKER_POOL_LIMIT=broker_pool_limit
```

### Running an Example Task

To run an example task and see distributaur in action, you can execute the example script provided in the project:

```bash
# To run the example task locally
python -m distributaur.example.local

# To run the example task on VAST.ai ("kitchen sink" example)
python -m distributaur.example.distributed

```

This script configures the environment, registers a sample function, dispatches a task, and monitors its execution.

### Command Options

Below are options you can pass into your distributaur example run.

- `--max_price` is the max price (in $/hour) a node can be be rented for.
- `--max_nodes` is the max number of vast.ai nodes that can be rented.
- `--docker_image` is the name of the docker image to load to the vast.ai node.
- `--module_name` is the name of the celery worker
- `--number_of_tasks` is the number of example tasks that will be added to the queue and done by the workers.

### Distributaur initialization

The Distributaur object is initialized with various settings. The ones that depend on the environment are taken from a .env or config.json file present in the parent directory. 

The following are other settings that deal directory with the Celery app or features for your convience of use:


Tasks are acknowledged after they are executed

`celery.app.tasks_acks_late = 1`

Worker only fetches one task at a time

`celery.app.worker_prefetch_multiplier = 1`

If task creation fails, retry 3 times, waiting 30 seconds between each retry

`celery.app.task.max_retries = 3`
`celery.app.default_retry_delay = 30`


### Overview of most useful API calls

Settings, Environment, and Help

- `create_from_config()` - create Distribtaur instance using environment
- `get_env(key)` - get value from .env
- `get_settings(key)` - get value from settings dictionary
- `log(message)` - log to console

Celery tasks

- `register_function(func)` - register function to be task for worker
- `execute_function(func_name, args)` - create Celery task using registered function

Redis server

- `get_redis_url()` - get Redis host url 
- `get_redis_connection()` - get Redis connection instance
 
Worker management with Vast.ai API

- `search_offers(max_price)` - search for available instances on Vast.ai
- `rent_nodes(max_price, max_nodes, image, module_name, command)` - rent nodes using Vast.ai instance
- `terminate_nodes(node_id_lists)` - terminate Vast.ai instance


HuggingFace repositories and uploading

- `initialize_dataset()` - intialize dataset repo on HuggingFace
- `upload_file(path_to_file)` - upload file to Huggingface
- `upload_directory(path_to_directory)` - upload folder to Huggingface repo
- `delete_file(path_to_file)` - delte file on HuggingFace repo

## Documentation of Required Packages

Celery: `https://docs.celeryq.dev/en/stable/`   
Redis: `https://redis.io/docs/latest/`