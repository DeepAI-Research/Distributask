import json
import os
import signal
import sys
import argparse
import time
from celery import chord, uuid

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../"))

from distributaur.vast import rent_nodes, terminate_nodes, monitor_job_status, handle_sigint, attach_to_existing_job, dump_redis_values
from distributaur.worker import render_object, notify_completion

def render_objects(
    job_id,
    start_index,
    end_index,
    start_frame=0,
    end_frame=65,
    width=1920,
    height=1080,
    output_dir="./renders",
    hdri_path="./backgrounds",
    max_price=0.1,
    max_nodes=1,
    image="arfx/simian-worker:latest",
    api_key=None,
):
    combinations = []
    # read combinations.json
    with open("combinations.json", "r") as file:
        combinations = json.load(file)
        combinations = combinations["combinations"]

    # make sure end_index is less than the number of combinations
    end_index = min(end_index, len(combinations))

    print(f"Rendering objects from {start_index} to {end_index}")

    tasks = [
        render_object.s(
            job_id,
            i,
            combination,
            width,
            height,
            output_dir,
            hdri_path,
            start_frame,
            end_frame,
        ) for i, combination in enumerate(combinations[start_index:end_index])
    ]
    callback = notify_completion.s(job_id)  # Pass job_id to completion callback
    job = chord(tasks)(callback)

    # Rent nodes using distributed_vast
    nodes = rent_nodes(max_price, max_nodes, image, api_key)

    # Set up signal handler for SIGINT
    signal.signal(signal.SIGINT, lambda sig, frame: handle_sigint(nodes))

    # Add delay to wait for workers to start
    time.sleep(30)  # Adjust this time as needed

    # Monitor the job status
    monitor_job_status(job)  # Directly pass the job

    # Dump Redis values for debugging
    # dump_redis_values()

    # Terminate nodes once the job is complete
    terminate_nodes(nodes)

    print("All tasks have been completed!")
    return job


def main():
    parser = argparse.ArgumentParser(
        description="Automate the rendering of objects using Celery."
    )
    parser.add_argument(
        "--start_index",
        type=int,
        default=0,
        help="Starting index for rendering from the combinations list.",
    )
    parser.add_argument(
        "--end_index",
        type=int,
        default=100,
        help="Ending index for rendering from the combinations list.",
    )
    parser.add_argument(
        "--start_frame",
        type=int,
        default=0,
        help="Starting frame number for the animation. Defaults to 0.",
    )
    parser.add_argument(
        "--end_frame",
        type=int,
        default=65,
        help="Ending frame number for the animation. Defaults to 65.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1920,
        help="Width of the rendering in pixels. Defaults to 1920.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1080,
        help="Height of the rendering in pixels. Defaults to 1080.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./renders",
        help="Directory to save rendered outputs. Defaults to './renders'.",
    )
    parser.add_argument(
        "--hdri_path",
        type=str,
        default="./backgrounds",
        help="Directory containing HDRI files for rendering. Defaults to './backgrounds'.",
    )
    parser.add_argument(
        "--max_price",
        type=float,
        default=0.1,
        help="Maximum price per hour for renting nodes. Defaults to 0.1.",
    )
    parser.add_argument(
        "--max_nodes",
        type=int,
        default=1,
        help="Maximum number of nodes to rent. Defaults to 1.",
    )
    parser.add_argument(
        "--image",
        type=str,
        default="arfx/simian-worker:latest",
        help="Docker image to use for rendering. Defaults to 'arfx/simian-worker:latest'.",
    )
    parser.add_argument(
        "--api_key",
        type=str,
        default=None,
        help="API key for renting nodes. Defaults to None.",
    )
    # add job_id
    parser.add_argument(
        "--job_id",
        type=str,
        default=str(uuid()),
        help="Unique job ID for the batch.",
    )

    args = parser.parse_args()

    job_id = args.job_id
    # Check if attaching to an existing job
    if attach_to_existing_job(job_id):
        # Monitor the job status
        monitor_job_status()
    else:
        render_objects(
            job_id=job_id,
            start_index=args.start_index,
            end_index=args.end_index,
            start_frame=args.start_frame,
            end_frame=args.end_frame,
            width=args.width,
            height=args.height,
            output_dir=args.output_dir,
            hdri_path=args.hdri_path,
            max_price=args.max_price,
            max_nodes=args.max_nodes,
            image=args.image,
            api_key=args.api_key,
        )

if __name__ == "__main__":
    main()
