FROM --platform=linux/x86_64 ubuntu:24.04

RUN apt-get update && \
    apt-get install -y \
    wget \
    xz-utils \
    bzip2 \
    git \
    git-lfs \
    python3-pip \
    python3 \
    && apt-get install -y software-properties-common

COPY requirements.txt .

RUN pip install -r requirements.txt --break-system-packages

COPY distributaur/ ./distributaur/
COPY example.py example.py
COPY example_worker.py example_worker.py
COPY config.json ./config.json

CMD ["celery", "-A", "example_worker", "worker", "--loglevel=info", "--concurrency=1"]