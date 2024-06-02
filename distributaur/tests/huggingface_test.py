import json
import os
import sys
import tempfile
from huggingface_hub import HfApi

current_dir = os.path.dirname(os.path.abspath(__file__))
combiner_path = os.path.join(current_dir, "../")
sys.path.append(combiner_path)

from distributaur.core import get_env_vars
from distributaur.huggingface import (
    initialize_repo,
    upload_directory,
    delete_file,
    file_exists,
    list_files,
)


def test_initialize_repo():
    env_vars = get_env_vars()
    hf_token = env_vars.get("HF_TOKEN") or os.getenv("HF_TOKEN")
    repo_id = env_vars.get("HF_REPO_ID") or os.getenv("HF_REPO_ID")

    # Initialize the repository
    initialize_repo(repo_id)

    # Check if the repository exists
    api = HfApi(token=hf_token)
    repo_info = api.repo_info(repo_id=repo_id, repo_type="dataset")
    assert repo_info["id"] == repo_id

    # Check if the config.json file exists in the repository
    repo_files = api.list_repo_files(
        repo_id=repo_id, repo_type="dataset", token=hf_token
    )
    assert "config.json" in repo_files

    # Clean up the repository
    api.delete_repo(repo_id=repo_id, repo_type="dataset", token=hf_token)


def test_upload_directory():
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        test_files = ["test1.txt", "test2.txt"]
        for file in test_files:
            file_path = os.path.join(temp_dir, file)
            with open(file_path, "w") as f:
                f.write("Test content")

        env_vars = get_env_vars()
        hf_token = env_vars.get("HF_TOKEN") or os.getenv("HF_TOKEN")
        repo_id = env_vars.get("HF_REPO_ID") or os.getenv("HF_REPO_ID")
        repo_path = env_vars.get("HF_PATH") or os.getenv("HF_PATH") or "data"

        # Upload the directory to the repository
        upload_directory(temp_dir, repo_path)

        # Check if the files exist in the Hugging Face repository
        api = HfApi(token=hf_token)
        repo_files = api.list_repo_files(
            repo_id=repo_id, repo_type="dataset", token=hf_token
        )
        for file in test_files:
            assert os.path.join(repo_path, file) in repo_files

        # Clean up the repository
        api.delete_repo(repo_id=repo_id, repo_type="dataset", token=hf_token)


def test_delete_file():
    env_vars = get_env_vars()
    hf_token = env_vars.get("HF_TOKEN") or os.getenv("HF_TOKEN")
    repo_id = env_vars.get("HF_REPO_ID") or os.getenv("HF_REPO_ID")

    # Create a test file in the repository
    test_file = "test.txt"
    api = HfApi(token=hf_token)
    api.upload_file(
        path_or_fileobj=test_file,
        path_in_repo=test_file,
        repo_id=repo_id,
        token=hf_token,
        repo_type="dataset",
    )

    # Delete the file from the repository
    delete_file(repo_id, test_file)

    # Check if the file is deleted from the repository
    repo_files = api.list_repo_files(
        repo_id=repo_id, repo_type="dataset", token=hf_token
    )
    assert test_file not in repo_files

    # Clean up the repository
    api.delete_repo(repo_id=repo_id, repo_type="dataset", token=hf_token)


def test_file_exists():
    env_vars = get_env_vars()
    hf_token = env_vars.get("HF_TOKEN") or os.getenv("HF_TOKEN")
    repo_id = env_vars.get("HF_REPO_ID") or os.getenv("HF_REPO_ID")

    # Create a test file in the repository
    test_file = "test.txt"
    api = HfApi(token=hf_token)
    api.upload_file(
        path_or_fileobj=test_file,
        path_in_repo=test_file,
        repo_id=repo_id,
        token=hf_token,
        repo_type="dataset",
    )

    # Check if the file exists in the repository
    assert file_exists(repo_id, test_file)

    # Check if a non-existent file exists in the repository
    assert not file_exists(repo_id, "nonexistent.txt")

    # Clean up the repository
    api.delete_repo(repo_id=repo_id, repo_type="dataset", token=hf_token)


def test_list_files():
    env_vars = get_env_vars()
    hf_token = env_vars.get("HF_TOKEN") or os.getenv("HF_TOKEN")
    repo_id = env_vars.get("HF_REPO_ID") or os.getenv("HF_REPO_ID")

    # Create test files in the repository
    test_files = ["test1.txt", "test2.txt"]
    api = HfApi(token=hf_token)
    for file in test_files:
        api.upload_file(
            path_or_fileobj=file,
            path_in_repo=file,
            repo_id=repo_id,
            token=hf_token,
            repo_type="dataset",
        )

    # List the files in the repository
    repo_files = list_files(repo_id)

    # Check if the test files are present in the repository
    for file in test_files:
        assert file in repo_files

    # Clean up the repository
    api.delete_repo(repo_id=repo_id, repo_type="dataset", token=hf_token)
