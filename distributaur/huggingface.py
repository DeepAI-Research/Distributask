import json
import os
from distributaur.core import get_env_vars
from huggingface_hub import HfApi, Repository
from requests.exceptions import HTTPError


def initialize_repo(repo_id: str, repo_type: str = "dataset", **kwargs) -> None:
    """Initialize a Hugging Face repository if it doesn't exist."""
    env_vars = get_env_vars()
    hf_token = os.getenv("HF_TOKEN") or env_vars.get("HF_TOKEN")
    api = HfApi(token=hf_token)

    try:
        repo_info = api.repo_info(repo_id=repo_id, repo_type=repo_type)
        print(f"Repository {repo_id} already exists.")
    except HTTPError as e:
        if e.response.status_code == 404:
            print(f"Repository {repo_id} does not exist. Creating a new repository.")
            api.create_repo(
                repo_id=repo_id, token=hf_token, repo_type=repo_type, **kwargs
            )
        else:
            raise e

    # Create config.json file
    config = {
        "data_loader_name": "custom",
        "data_loader_kwargs": {
            "path": repo_id,
            "format": "files",
            "fields": ["file_path", "text"],
        },
    }

    with Repository(
        local_dir=".",
        clone_from=repo_id,
        repo_type=repo_type,
        use_auth_token=hf_token,
    ).commit(commit_message="Add config.json"):
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)

    print(f"Initialized repository {repo_id} with config.json.")


def upload_directory(output_dir: str, repo_dir: str) -> None:
    """Upload the rendered outputs to a Huggingface repository."""
    env_vars = get_env_vars()
    hf_token = os.getenv("HF_TOKEN") or env_vars.get("HF_TOKEN")
    repo_id = os.getenv("HF_REPO_ID") or env_vars.get("HF_REPO_ID")

    # Initialize the repository if it doesn't exist
    initialize_repo(repo_id)

    api = HfApi(token=hf_token)

    for root, dirs, files in os.walk(output_dir):
        for file in files:
            local_path = os.path.join(root, file)
            path_in_repo = os.path.join(repo_dir, file) if repo_dir else file

            try:
                print(
                    f"Uploading {local_path} to Hugging Face repo {repo_id} at {path_in_repo}"
                )
                api.upload_file(
                    path_or_fileobj=local_path,
                    path_in_repo=path_in_repo,
                    repo_id=repo_id,
                    token=hf_token,
                    repo_type="dataset",
                )
                print(
                    f"Uploaded {local_path} to Hugging Face repo {repo_id} at {path_in_repo}"
                )
            except Exception as e:
                print(
                    f"Failed to upload {local_path} to Hugging Face repo {repo_id} at {path_in_repo}: {e}"
                )


def delete_file(repo_id: str, path_in_repo: str, repo_type: str = "dataset") -> None:
    """Delete a file from a Hugging Face repository."""
    env_vars = get_env_vars()
    hf_token = os.getenv("HF_TOKEN") or env_vars.get("HF_TOKEN")
    api = HfApi(token=hf_token)

    try:
        api.delete_file(
            repo_id=repo_id,
            path_in_repo=path_in_repo,
            repo_type=repo_type,
            token=hf_token,
        )
        print(f"Deleted {path_in_repo} from Hugging Face repo {repo_id}")
    except Exception as e:
        print(f"Failed to delete {path_in_repo} from Hugging Face repo {repo_id}: {e}")


def file_exists(repo_id: str, path_in_repo: str, repo_type: str = "dataset") -> bool:
    """Check if a file exists in a Hugging Face repository."""
    env_vars = get_env_vars()
    hf_token = os.getenv("HF_TOKEN") or env_vars.get("HF_TOKEN")
    api = HfApi(token=hf_token)

    try:
        repo_files = api.list_repo_files(
            repo_id=repo_id, repo_type=repo_type, token=hf_token
        )
        return path_in_repo in repo_files
    except Exception as e:
        print(
            f"Failed to check if {path_in_repo} exists in Hugging Face repo {repo_id}: {e}"
        )
        return False


def list_files(repo_id: str, repo_type: str = "dataset") -> list:
    """Get a list of files from a Hugging Face repository."""
    env_vars = get_env_vars()
    hf_token = os.getenv("HF_TOKEN") or env_vars.get("HF_TOKEN")
    api = HfApi(token=hf_token)

    try:
        repo_files = api.list_repo_files(
            repo_id=repo_id, repo_type=repo_type, token=hf_token
        )
        return repo_files
    except Exception as e:
        print(f"Failed to get the list of files from Hugging Face repo {repo_id}: {e}")
        return []
