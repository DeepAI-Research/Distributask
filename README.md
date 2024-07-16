# Distributask 


A simple way to distribute rendering tasks across multiple machines.

[![Lint and Test](https://https://github.com/DeepAI-Research/Distributask/actions/workflows/test.yml/badge.svg)](https://github.com/DeepAI-Research/Distributask/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/distributask.svg)](https://badge.fury.io/py/distributask)
[![License](https://img.shields.io/badge/License-MIT-blue)](https://github.com/RaccoonResearch/distributask/blob/main/LICENSE)
[![forks - distributask](https://img.shields.io/github/forks/RaccoonResearch/distributask?style=social)](https://github.com/RaccoonResearch/distributask)

# Description

Distributask is a package that automatically queues, executes, and uploads the result of any task you want using Vast.ai, a decentralized network of GPUs. It works by first creating a Celery queue of the tasks, which is code that you want to be ran on a GPU. The tasks are then passed to the Vast.ai GPU workers using Redis as a message broker. Once the worker has completed the task, the result is uploaded to Huggingface.

# Installation

```bash
pip install distributask
```

# Development

### Setup

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/DeepAI-Research/Distributask.git
cd Distributask
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Install the distributask package:

```bash
python setup.py install
```

### Configuration

Create a `.env` file in the root directory of your project or set environment variables to create your desired setup:

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

## Getting Started

### Running an Example Task

To run an example task and see Distributask in action, you can execute the example script provided in the project:

```bash
# Run the example task locally using either a Docker container or a Celery worker:
python -m distributask.example.local

# Run the example task on Vast.ai ("kitchen sink" example):
python -m distributask.example.distributed

```

This script configures the environment, registers a sample function, creats a queue of tasks, and monitors its execution on some workers.

### Command Options

- `--max_price` is the max price (in $/hour) a node can be be rented for.
- `--max_nodes` is the max number of vast.ai nodes that can be rented.
- `--docker_image` is the name of the docker image to load to the vast.ai node.
- `--module_name` is the name of the Celery worker.
- `--number_of_tasks` is the number of example tasks that will be added to the queue and done by the workers.

## More Info

Check out our in-depth documentation at deepai-research.github.io/Distributask/!

## Contributing

Contributions are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Citation

```bibtex
@misc{Distributask,
  author = {DeepAIResearch},
  title = {Distributask: a simple way to distribute rendering tasks across mulitiple machines},
  year = {2024},
  publisher = {GitHub},
  howpublished = {\url{https://github.com/RaccoonResearch/distributask}}
}
```

## Contributors

<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/lalalune"><img src="https://avatars.githubusercontent.com/u/18633264?v=4?s=100" width="100px;" alt="M̵̞̗̝̼̅̏̎͝Ȯ̴̝̻̊̃̋̀Õ̷̼͋N̸̩̿͜ ̶̜̠̹̼̩͒"/><br /><sub><b>M̵̞̗̝̼̅̏̎͝Ȯ̴̝̻̊̃̋̀Õ̷̼͋N̸̩̿͜ ̶̜̠̹̼̩͒</b></sub></a><br />
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/antbaez9"><img src="https://avatars.githubusercontent.com/u/97056049?v=4?s=100" width="100px;" alt="Anthony"/><br /><sub><b>Anthony</b></sub></a><br /></td>
    </tr>
  </tbody>
</table>