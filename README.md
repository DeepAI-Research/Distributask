# distributaur <a href="https://discord.gg/qetWd7J9De"><img style="float: right" src="https://dcbadge.vercel.app/api/server/JMfbmHdPNB" alt=""></a> <a href="https://github.com/RaccoonResearch/distributaur/stargazers"><img style="float: right; padding: 5px;" src="https://img.shields.io/github/stars/RaccoonResearch/distributaur?style=social" alt=""></a>

A super simple way to distribute rendering tasks across multiple machines.

<img src="docs/assets/banner.png">

[![Lint and Test](https://github.com/RaccoonResearch/distributaur/actions/workflows/test.yml/badge.svg)](https://github.com/RaccoonResearch/distributaur/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/distributaur.svg)](https://badge.fury.io/py/distributaur)
[![License](https://img.shields.io/badge/License-MIT-blue)](https://github.com/RaccoonResearch/distributaur/blob/main/LICENSE)
[![forks - distributaur](https://img.shields.io/github/forks/RaccoonResearch/distributaur?style=social)](https://github.com/RaccoonResearch/distributaur)

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
celery -A distributaur.core worker --loglevel=info
```

### Running an Example Task

To run an example task and see Distributaur in action, you can execute the example script provided in the project:

```bash
python example.py
```

This script configures the environment, registers a sample function, dispatches a task, and monitors its execution.

## API Reference

### Core Functionality

- **register_function(func)**: Decorator to register a function that can be called as a task.
- **execute_function(func_name, args)**: Dispatch a registered function as a task with specified arguments.

### Task Management

- **update_function_status(task_id, status)**: Update the status of a task in Redis.
- **monitor_job_status(job_id)**: Monitor the status of a job and output updates.

### VAST.ai Integration

- **rent_nodes(max_price, max_nodes, image, api_key)**: Rent nodes from VAST.ai based on specified criteria.
- **terminate_nodes(nodes)**: Terminate rented nodes on VAST.ai.

## Contributing

Contributions are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.