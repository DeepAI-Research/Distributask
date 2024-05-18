import argparse
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))

from distributaur.core import submit_task

def main():
    parser = argparse.ArgumentParser(description="Distributaur CLI")
    parser.add_argument("--code", type=str, help="Python code to execute.")
    args = parser.parse_args()

    result = submit_task(args.code)
    print(f"Execution Result: {result}")

if __name__ == "__main__":
    main()
