import argparse
import datetime
import inspect
import logging
import operator
import os
import re
import shutil
import signal
import subprocess
import sys
from contextlib import suppress
from pathlib import Path
from subprocess import Popen
from typing import Any, Dict, List, Optional, Tuple

import click

BENCHMARK_ROOT = Path(inspect.getframeinfo(inspect.currentframe()).filename).parent.parent  # type: ignore
REPO_ROOT = BENCHMARK_ROOT.parent


nan = float("nan")
CTRL_C_EXIT_CODE = -15
TSV_FILENAME = "output.tsv"


def is_valid_file(arg):
    """Argparse validator for files to check for their existence."""
    if not os.path.exists(arg):
        raise FileNotFoundError("The file %s does not exist!" % arg)
    return Path(arg).absolute()


def get_argparser(description: str = "", use_dataset: bool = True):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-p", "--program", dest="program_path", type=is_valid_file, required=True
    )
    if use_dataset:
        parser.add_argument(
            "-d",
            "--dataset",
            dest="dataset_paths",
            type=is_valid_file,
            nargs="*",
            required=True,
        )
    parser.add_argument(
        "-w", "--working-dir", dest="working_dir", type=str, default=None
    )
    return parser


def to_seconds(millis: float) -> float:
    """From milliseconds to seconds."""
    return millis / 1000.0


def try_to_get_float(pattern: str, text: str, default=-1.0) -> float:
    """Try to extract a float number from text."""
    number_match = re.search(pattern, text)
    number = float(number_match.group(1)) if number_match else default
    return number


def get_tools(benchmark_dir: Path, order: Optional[List[str]] = None):
    tool_to_tsv = {}
    tool_dirs = list(filter(operator.methodcaller("is_dir"), benchmark_dir.iterdir()))
    if order:
        tool_dirs = sorted(
            tool_dirs, key=lambda x: -1 if x.name not in order else order.index(x.name)
        )
    for tool_dir in tool_dirs:
        tsv_files = list(tool_dir.glob("*.tsv"))
        assert len(tsv_files) == 1
        tsv_file = tsv_files[0]
        tool_to_tsv[tool_dir.name] = tsv_file
    return tool_to_tsv


def configure_logging(filename: Optional[str] = None):
    console = logging.StreamHandler()
    handlers = [console]
    if filename:
        file = logging.FileHandler(filename)
        handlers += [file]
    logging.basicConfig(
        format="[%(asctime)s][%(levelname)s]: %(message)s",
        level=logging.DEBUG,
        handlers=handlers,
    )


def default_output_dir(file_name):
    return Path("results") / (
        Path(file_name).stem + "-" + datetime.datetime.now().isoformat()
    )


def launch(cmd: List[str], cwd: Optional[str] = None) -> Popen:
    """Launch a command."""
    print("Running command: ", " ".join(map(str, cmd)))
    process = Popen(
        args=cmd, encoding="utf-8", cwd=cwd, stdout=sys.stdout, stderr=sys.stdout
    )
    try:
        process.wait()
    except KeyboardInterrupt:
        print("Interrupted")
        process.terminate()
        with suppress(subprocess.TimeoutExpired):
            process.wait(timeout=10.0)
    finally:
        if process.poll() is None:
            os.kill(process.pid, signal.SIGKILL)
            process.wait()
    return process


def ask_before_removing_directory(directory_to_remove: Path) -> bool:
    return click.prompt(
        f"Are you sure you want to remove directory {directory_to_remove}?",
        default=True,
    )


def remove_dir_or_fail(output_dir: Path, force: bool):
    if force:
        shutil.rmtree(output_dir, ignore_errors=True)
        return
    if output_dir.exists():
        if ask_before_removing_directory(output_dir):
            shutil.rmtree(output_dir)
        else:
            click.echo("Directory not removed, cannot continue.")
            exit(1)


def ensure(value, default) -> Any:
    """Ensure 'value' is not None; if None, return default."""
    return value if value is not None else default


def ensure_dict(value: Optional[Dict]) -> Dict:
    """Ensure value is a dict; if None, return empty dict."""
    return ensure(value, {})
