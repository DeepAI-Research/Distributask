import argparse
import os
import sys
from distributaur.batch import render_objects, main as batch_main
from distributaur.vast import check_job_status, redis_client

def prompt_user_settings():
    settings = {}
    settings['start_index'] = int(input("Starting index for rendering (default: 0): ") or 0)
    settings['end_index'] = int(input("Ending index for rendering (default: 100): ") or 100)
    settings['start_frame'] = int(input("Starting frame number (default: 0): ") or 0)
    settings['end_frame'] = int(input("Ending frame number (default: 65): ") or 65)
    settings['width'] = int(input("Rendering width in pixels (default: 1920): ") or 1920)
    settings['height'] = int(input("Rendering height in pixels (default: 1080): ") or 1080)
    settings['output_dir'] = input("Output directory (default: './renders'): ") or './renders'
    settings['hdri_path'] = input("HDRI path (default: './backgrounds'): ") or './backgrounds'
    settings['max_price'] = float(input("Maximum price per hour (default: 0.1): ") or 0.1)
    settings['max_nodes'] = int(input("Maximum number of nodes (default: 1): ") or 1)
    settings['image'] = input("Docker image (default: 'arfx/simian-worker:latest'): ") or 'arfx/simian-worker:latest'
    settings['api_key'] = input("Vast.ai API key (default: None): ")

    settings['redis_host'] = input("Redis host (default: 'localhost'): ") or 'localhost'
    settings['redis_port'] = int(input("Redis port (default: 6379): ") or 6379)
    settings['redis_user'] = input("Redis user (default: ''): ")
    settings['redis_password'] = input("Redis password (default: ''): ")
    settings['hf_token'] = input("Hugging Face token (default: ''): ")
    settings['hf_repo_id'] = input("Hugging Face repository ID (default: ''): ")
    settings['hf_path'] = input("Hugging Face path (default: ''): ")

    return settings

def start_new_job(args):
    print("Starting a new job...")
    settings = prompt_user_settings()
    job_id = input("Enter a unique job ID: ")

    # Override environment variables with provided arguments
    os.environ['REDIS_HOST'] = args.redis_host or settings['redis_host'] or os.environ.get('REDIS_HOST', 'localhost')
    os.environ['REDIS_PORT'] = str(args.redis_port or settings['redis_port'] or os.environ.get('REDIS_PORT', 6379))
    os.environ['REDIS_USER'] = args.redis_user or settings['redis_user'] or os.environ.get('REDIS_USER', '')
    os.environ['REDIS_PASSWORD'] = args.redis_password or settings['redis_password'] or os.environ.get('REDIS_PASSWORD', '')
    os.environ['HF_TOKEN'] = args.hf_token or settings['hf_token'] or os.environ.get('HF_TOKEN', '')
    os.environ['HF_REPO_ID'] = args.hf_repo_id or settings['hf_repo_id'] or os.environ.get('HF_REPO_ID', '')
    os.environ['HF_PATH'] = args.hf_path or settings['hf_path'] or os.environ.get('HF_PATH', '')

    render_objects(job_id=job_id, **settings)

def list_jobs():
    # ... (rest of the list_jobs function remains the same)

def main():
    parser = argparse.ArgumentParser(description="Simian CLI")
    parser.add_argument('action', choices=['start', 'list'], help="Action to perform")
    parser.add_argument('--redis-host', help="Redis host")
    parser.add_argument('--redis-port', type=int, help="Redis port")
    parser.add_argument('--redis-user', help="Redis user")
    parser.add_argument('--redis-password', help="Redis password")
    parser.add_argument('--hf-token', help="Hugging Face token")
    parser.add_argument('--hf-repo-id', help="Hugging Face repository ID")
    parser.add_argument('--hf-path', help="Hugging Face path")
    args = parser.parse_args()

    if args.action == 'start':
        start_new_job(args)
    elif args.action == 'list':
        list_jobs()

def list_jobs():
    job_keys = redis_client.keys("celery-task-meta-*")
    jobs = {}
    for key in job_keys:
        job_id = key.decode('utf-8').split('-')[-1]
        if job_id not in jobs:
            jobs[job_id] = check_job_status(job_id)

    if not jobs:
        print("No existing jobs found.")
        return

    print("Existing jobs:")
    for job_id, status_counts in jobs.items():
        print(f"Job ID: {job_id}")
        print(f"  Status: {status_counts}")
        print()

    while True:
        selection = input("Enter a job ID to attach to, 'd' to delete a job, 'c' to clear all jobs, or 'q' to quit: ")
        if selection == 'q':
            break
        elif selection == 'c':
            confirm = input("Are you sure you want to clear all jobs? (y/n): ")
            if confirm.lower() == 'y':
                redis_client.flushdb()
                print("All jobs cleared.")
            break
        elif selection == 'd':
            job_id = input("Enter the job ID to delete: ")
            if job_id in jobs:
                keys = redis_client.keys(f"celery-task-meta-*{job_id}")
                for key in keys:
                    redis_client.delete(key)
                print(f"Job {job_id} deleted.")
            else:
                print(f"Job {job_id} not found.")
        elif selection in jobs:
            print(f"Attaching to job {selection}...")
            sys.argv = [sys.argv[0], '--job_id', selection]
            batch_main()
            break
        else:
            print("Invalid selection.")

if __name__ == "__main__":
    main()