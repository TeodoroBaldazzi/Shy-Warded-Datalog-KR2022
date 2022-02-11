import argparse
import dataclasses
import json
import logging
import os
import signal
import subprocess
import time
from json import JSONDecodeError
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from benchmark import ROOT_DIR
from benchmark.tools.core import Result, Status, Tool

DEFAULT_JAVA_HOME = (
    Path(os.getenv("HOME")) / ".sdkman" / "candidates" / "java" / "current"
)
DEFAULT_VADALOG_ROOT = ROOT_DIR / "third_party" / "vadalog-engine-bankitalia"
DEFAULT_VADALOG_URL = "http://localhost:8080"
VADALOG_WRAPPER_PATH = ROOT_DIR / "bin" / "vadalog-wrapper"


class VadalogTool(Tool):
    """Implement the Vadalog tool wrapper."""

    NAME = "Vadalog"

    def __init__(self, binary_path: str) -> None:
        super().__init__(binary_path)

        self.vadalog_server = _VadalogServer()

    def collect_statistics(self, output: str) -> Result:
        try:
            json_output = json.loads(output)
            result_set = json_output["resultSet"]
            result_sets = list(result_set.items())
            if len(result_sets) == 0:
                nb_values = 0
            else:
                nb_values = len(result_sets[0][1])
            return Result(status=Status.SUCCESS, nb_atoms=nb_values)
        except json.JSONDecodeError:
            return Result(status=Status.ERROR)

    def get_cli_args(
        self,
        program: Path,
        datasets: List[Path],
        run_config: Dict,
        working_dir: Optional[str] = None,
    ) -> List[str]:
        bind_parameters: List[str] = run_config["binds"]
        args = [self.binary_path, "--program", program]
        if len(bind_parameters) > 0:
            args += ["--bind", *bind_parameters]
        if working_dir is not None:
            args += ["--working-dir", working_dir]
        return args

    def start_session(self) -> None:
        if self.vadalog_server.is_running:
            return
        print("Start Vadalog server")
        self.vadalog_server.start()

    def end_session(self) -> None:
        if not self.vadalog_server.is_running:
            return
        print("Stop Vadalog server")
        self.vadalog_server.stop()


class _VadalogServer:
    def __init__(
        self,
        java_home: Path = DEFAULT_JAVA_HOME,
        vadalog_root: Path = DEFAULT_VADALOG_ROOT,
    ):
        self.java_home = java_home
        self.vadalog_root = vadalog_root
        self.vadalog_server: Optional[subprocess.Popen] = None

    @property
    def java_bin(self) -> Path:
        """Get the java binary."""
        return self.java_home / "bin" / "java"

    @property
    def is_running(self) -> bool:
        return self.vadalog_server is not None

    def start(self):
        if self.is_running:
            return
        logging.info("Starting Vadalog engine server...")
        self.vadalog_server = subprocess.Popen(
            [str(self.java_bin), "-jar", "target/VadaEngine-1.10.6.jar"],
            cwd=str(self.vadalog_root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logging.info("Wait until Vadalog server is healthy...")
        try:
            self.wait_until_up()
            logging.info("Vadalog is ready!")
        except TimeoutError:
            self._stop()
            raise

    def stop(self):
        if not self.is_running:
            return
        self._stop()

    def _stop(self):
        self.vadalog_server.terminate()
        try:
            self.vadalog_server.wait(timeout=10.0)
        except subprocess.TimeoutExpired:
            if self.vadalog_server.poll() is None:
                os.kill(self.vadalog_server.pid, signal.SIGKILL)
        finally:
            self.vadalog_server = None

    def wait_until_up(self, timeout: float = 1.0, attempts=10):
        for i in range(attempts):
            try:
                response = requests.get(DEFAULT_VADALOG_URL)
                response.json()
                return
            except (requests.ConnectionError, JSONDecodeError):
                time.sleep(timeout)
        raise TimeoutError("Vadalog engine does not respond")


@dataclasses.dataclass(frozen=True)
class Bind:
    predicate_name: str
    dataset_format: str
    dataset_path: Path

    def to_input_statement(self) -> str:
        return f'@input("{self.predicate_name}").'

    def to_vadalog_statement(self) -> str:
        return f'@bind("{self.predicate_name}", "{self.dataset_format}", "{self.dataset_path.parent}", "{self.dataset_path.name}").'


def parse_bind_type(arg: str) -> Bind:
    """
    Argparse validator for bind parameters.

    A bind parameter has the form:

        predicate_name:data_format:dataset_path

    e.g.:

        own:csv:/path/to/company_control/relationships.csv

    :param arg: the argument.
    :return: the predicate name, the format, the dataset path.
    """
    tokens = arg.split(":")
    if len(tokens) != 3:
        raise argparse.ArgumentTypeError(
            f"expected 3 tokens, got {len(tokens)}: {tokens}"
        )
    predicate_name, dataset_format, dataset_path = tokens
    dataset_path = Path(dataset_path).absolute()
    if not dataset_path.is_file():
        raise argparse.ArgumentTypeError(
            f"the dataset path provided is not a file: {dataset_path}"
        )
    return Bind(predicate_name, dataset_format, dataset_path)
