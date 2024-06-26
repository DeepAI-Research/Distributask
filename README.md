# distributaur 

<!-- <a href="https://discord.gg/JMfbmHdPNB"><img style="float: right" src="https://dcbadge.vercel.app/api/server/JMfbmHdPNB" alt=""></a> <a href="https://github.com/RaccoonResearch/distributaur/stargazers"><img style="float: right; padding: 5px;" src="https://img.shields.io/github/stars/RaccoonResearch/distributaur?style=social" alt=""></a> -->

A simple way to distribute rendering tasks across multiple machines.

<img src="docs/assets/banner.png">

[![Lint and Test](https://github.com/RaccoonResearch/distributaur/actions/workflows/test.yml/badge.svg)](https://github.com/RaccoonResearch/distributaur/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/distributaur.svg)](https://badge.fury.io/py/distributaur)
[![License](https://img.shields.io/badge/License-MIT-blue)](https://github.com/RaccoonResearch/distributaur/blob/main/LICENSE)
[![forks - distributaur](https://img.shields.io/github/forks/RaccoonResearch/distributaur?style=social)](https://github.com/RaccoonResearch/distributaur)

# Description

Distributaur distributes rendering using the Celery task queue. The queued tasks are then passed to workers using Redis as a message broker. Once the worker has completed the task, the result is uploaded to Huggingface.

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

To run an example task and see Distributaur in action, you can execute the example script provided in the project:

```bash
# To run the example task locally using either a Docker container or a Celery worker
python -m distributaur.example.local

# To run the example task on vast.ai ("kitchen sink" example)
python -m distributaur.example.distributed

```

This script configures the environment, registers a sample function, dispatches a task, and monitors its execution.

### Command Options

- `--max_price` is the max price (in $/hour) a node can be be rented for.
- `--max_nodes` is the max number of vast.ai nodes that can be rented.
- `--docker_image` is the name of the docker image to load to the vast.ai node.
- `--module_name` is the name of the celery worker
- `--number_of_tasks` is the number of example tasks that will be added to the queue and done by the workers.

## Contributing

Contributions are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Citation

```bibtex
@misc{distributaur,
  author = {Raccoon Research},
  title = {distributaur: a simple way to distribute rendering tasks across mulitiple machines},
  year = {2024},
  publisher = {GitHub},
  howpublished = {\url{https://github.com/RaccoonResearch/distributaur}}
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