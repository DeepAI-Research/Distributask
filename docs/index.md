


<img src="assets/banner.png" style="width: 100%">

Distributaur is a simple way to distribute rendering tasks across multiple machines.

This documentation is intended to help you understand the structure of the distributaur API and codebase and how to use it to distribute rendering tasks across multiple machines for your own projects.

## Core Use Cases
distributaur can be used for any task that can is parallelizable. Some specific use cases include:

- Rendering videos
- Running simulations
- Generating or processing large datasets

## Getting Started

Visit the [Getting Started](getting_started.md) page to learn how to set up your environment and get started with distributing with distributaur.

## Overview

Distributed rendering using distributaur can be broken into four steps:

#### Creating the task queue

distributaur uses Celery, an asyncronous distributed task processing package, to create the task queue on your local machine. Each task on the queue is a function that tells remote machines, or workers, what to do. For example, if we wanted to render videos, each task would be a function that contains the code to render a different video.

#### Passing the tasks to workers

distributaur uses Redis, a data structure that can be used as a database, as a message broker. This means that Redis is used to transfer tasks yet to be done from the task queue to the worker so that the job can be done.

#### Executing the tasks

distributaur uses Vast.ai, a decentralized GPU market, to create workers that execute the task. The task is given to the worker, executed, and the completed task status is passed back to the central machine via Redis.

#### Storing results of the tasks

distributaur uses Huggingface, a platform for sharing AI models and datasets, to store the results of the task. The results of the task are uploaded to Hugginface using API calls in distributaur. For example, our rendered videos would be uploaded as a dataset on Huggingface.


