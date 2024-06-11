#!/bin/bash

# Define the port you want to kill connections for
PORT=54235

# Use lsof to find all PIDs for the given port and store them in an array
PIDS=($(lsof -i TCP:$PORT -t))

# Check if there are any PIDs to kill
if [ ${#PIDS[@]} -eq 0 ]; then
  echo "No processes found using port $PORT."
  exit 0
fi

# Loop through each PID and kill it
for PID in "${PIDS[@]}"; do
  echo "Killing process $PID"
  sudo kill -9 $PID
done

echo "All processes using port $PORT have been killed."
