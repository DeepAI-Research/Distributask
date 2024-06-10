# distributaur <a href="https://discord.gg/JMfbmHdPNB"><img style="float: right" src="https://dcbadge.vercel.app/api/server/JMfbmHdPNB" alt=""></a> <a href="https://github.com/RaccoonResearch/distributaur/stargazers"><img style="float: right; padding: 5px;" src="https://img.shields.io/github/stars/RaccoonResearch/distributaur?style=social" alt=""></a>

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
HF_TOKEN=hf_token
HF_REPO_ID=YourHFRepo/test_dataset
```

## Getting Started

### Running an Example Task

To run an example task and see Distributaur in action, you can execute the example script provided in the project:

```bash
# To run the example task locally
python -m distributaur.example.local

# To run the example task on VAST.ai ("kitcen sink" example)
python -m distributaur.example.distributed

```

This script configures the environment, registers a sample function, dispatches a task, and monitors its execution.

## API Reference

### Core Functionality

- **register_function(func: callable) -> callable**: Decorator to register a function so that it can be invoked as a task.
- **execute_function(func_name: str, args: dict) -> Celery.AsyncResult**: Execute a registered function as a Celery task with provided arguments.

### Configuration Management

- **get_env(key: str, default: any = None) -> any**: Retrieve a value from the configuration settings, with an optional default if the key is not found.

### Task Management

- **update_function_status(task_id: str, status: str) -> None**: Update the status of a function task in Redis.

### Hugging Face Dataset Management

- **initialize_dataset(**kwargs) -> None**: Initialize a Hugging Face repository if it doesn't exist.
- **upload_file(file_path: str) -> None**: Upload a file to a Hugging Face repository.
- **upload_directory(output_dir: str, repo_dir: str) -> None**: Upload the rendered outputs to a Hugging Face repository.
- **delete_file(repo_id: str, path_in_repo: str) -> None**: Delete a file from a Hugging Face repository.
- **file_exists(repo_id: str, path_in_repo: str) -> bool**: Check if a file exists in a Hugging Face repository.
- **list_files(repo_id: str) -> list**: Get a list of files from a Hugging Face repository.

### VAST.ai Integration

- **search_offers(max_price: float) -> List[Dict]**: Search for available offers on the Vast.ai platform.
- **create_instance(offer_id: str, image: str, module_name: str) -> Dict**: Create an instance on the Vast.ai platform.
- **destroy_instance(instance_id: str) -> Dict**: Destroy an instance on the Vast.ai platform.
- **rent_nodes(max_price: float, max_nodes: int, image: str, module_name: str) -> List[Dict]**: Rent nodes on the Vast.ai platform.
- **terminate_nodes(nodes: List[Dict]) -> None**: Terminate the rented nodes.

### Monitoring

- **start_monitoring_server(worker_name: str = "distributaur.example.worker") -> None**: Start Flower monitoring in a separate process.
- **stop_monitoring_server() -> None**: Stop Flower monitoring by terminating the Flower process.

## Contributing

Contributions are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.