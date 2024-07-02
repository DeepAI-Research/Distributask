# Getting Started

Below are instructions to get distributaur running on your machine. Please read through the rest of the documentation for more detailed information.

## Installation

```bash
pip install distributaur
```

## Development

### Prerequisites

- Python 3.8 or newer (tested on Python 3.11)
- Redis server
- Vast.ai API key
- HuggingFace API key


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
# Run an example task locally
python -m distributaur.example.local

# Run an example task on Vast.ai ("kitchen sink" example)
python -m distributaur.example.distributed
```

### Command Options

Below are options you can pass into your distributaur example run.

- `--max_price` is the max price (in $/hour) a node can be be rented for.
- `--max_nodes` is the max number of vast.ai nodes that can be rented.
- `--docker_image` is the name of the docker image to load to the vast.ai node.
- `--module_name` is the name of the celery worker
- `--number_of_tasks` is the number of example tasks that will be added to the queue and done by the workers.