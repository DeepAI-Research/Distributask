#!/bin/bash


# Load environment variables from .env file
source .env

# Check if REDIS_PORT is set in the .env file
if [ -z "$REDIS_PORT" ]; then
  echo "REDIS_PORT not found in .env file. Please set it and try again."
  exit 1
fi

# Use lsof to find all PIDs for the given port and store them in an array
PIDS=($(lsof -i TCP:$REDIS_PORT -t))

# Check if there are any PIDs to kill
if [ ${#PIDS[@]} -eq 0 ]; then
  echo "No processes found using port $REDIS_PORT."
  exit 0
fi

# Loop through each PID and kill it
for PID in "${PIDS[@]}"; do
  echo "Killing process $PID"
  sudo kill -9 $PID
done

echo "All processes using port $REDIS_PORT have been killed."