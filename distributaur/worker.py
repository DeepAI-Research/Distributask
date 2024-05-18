import json
import os
import subprocess
from distributaur.task_runner import run_task
from distributaur.utils import get_blender_path, upload_outputs

@run_task
def render_object(
    combination_index: int,
    combination: list,
    width: int,
    height: int,
    output_dir: str,
    hdri_path: str,
    start_frame: int = 0,
    end_frame: int = 65,
) -> None:
    combination = json.dumps(combination)
    combination = "\"" + combination.replace('"', '\\"') + "\""

    print("output_dir is", output_dir)

    os.makedirs(output_dir, exist_ok=True)

    args = f"--width {width} --height {height} --combination_index {combination_index}"
    args += f" --output_dir {output_dir}"
    args += f" --hdri_path {hdri_path}"
    args += f" --start_frame {start_frame} --end_frame {end_frame}"
    args += f" --combination {combination}"

    print("Args: ", args)

    application_path = get_blender_path()

    command = f"{application_path} --background --python simian/render.py -- {args}"
    print("Worker running: ", command)

    subprocess.run(["bash", "-c", command], check=False)

    upload_outputs(output_dir)

    for file in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)