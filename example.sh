#!/bin/bash

# Define log files
CELERY_LOG="celery.log"
EXAMPLE_LOG="example.log"

# Function to start the Celery worker
start_celery() {
    celery -A distributaur.task_runner worker --loglevel=info > $CELERY_LOG 2>&1
}

# Function to start the example script
start_example() {
    python distributaur/example.py > $EXAMPLE_LOG 2>&1
}

# Function to display logs
display_logs() {
    tail -f $CELERY_LOG & CELERY_TAIL_PID=$!
    tail -f $EXAMPLE_LOG & EXAMPLE_TAIL_PID=$!
    wait $CELERY_TAIL_PID $EXAMPLE_TAIL_PID
}

# Function to handle cleanup on script exit
cleanup() {
    echo "Stopping Celery worker and example script..."
    pkill -f "celery -A distributaur.task_runner worker"
    pkill -f "python distributaur/example.py"
    pkill -f "tail -f $CELERY_LOG"
    pkill -f "tail -f $EXAMPLE_LOG"
}

# Trap SIGINT and SIGTERM to call cleanup
trap cleanup SIGINT SIGTERM

# Start the Celery worker and example script in separate subshells
(start_celery) &
(start_example) &

# Wait for a few seconds to allow the processes to start
sleep 5

# Display logs from both processes
display_logs