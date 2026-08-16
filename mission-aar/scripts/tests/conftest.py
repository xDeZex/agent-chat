import json
import subprocess
import sys


def run_cli(script_path, *args):
    result = subprocess.run(
        [sys.executable, str(script_path), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)
