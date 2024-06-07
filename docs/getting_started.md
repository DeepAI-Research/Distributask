# Getting Started

Below are some quick notes to get you up and running. Please read through the rest of the documentation for more detailed information.

# Installation

```bash
pip install distributaur
```

# Development

### Prerequisites

- Python 3.8 or newer (tested on 3.10)
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
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_USER=user
REDIS_PASSWORD=password
VAST_API_KEY=your_vast_api_key
```

## Getting Started

### Starting the Worker

To start processing tasks, you need to run a worker. You can start a worker using the provided script:

```bash
sh scripts/kill_redis_connections.sh  # Optional: to clear previous Redis connections
celery -A distributaur.distributaur worker --loglevel=info
```

### Running an Example Task

To run an example task and see Distributaur in action, you can execute the example script provided in the project:

```bash
# To run the example task locally
python -m distributaur.example.local

# To run the example task on VAST.ai ("kitcen sink" example)
python -m distributaur.example.distributed

```

This script configures the environment, registers a sample function, dispatches a task, and monitors its execution.