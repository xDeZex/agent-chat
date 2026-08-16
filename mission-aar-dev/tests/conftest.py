import importlib.machinery
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

MISSION_AAR_DIR = Path(__file__).parent.parent.parent / "mission-aar"


def run_cli(script_path, *args):
    result = subprocess.run(
        [sys.executable, str(script_path), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def load_module(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_file_location(name, path, loader=loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module
