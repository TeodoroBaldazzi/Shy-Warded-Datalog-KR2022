import logging
import os
import signal
import subprocess
import time
from abc import ABC, abstractmethod
from contextlib import suppress
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from benchmark.utils.base import ensure_dict

SHUTDOWN_TIMEOUT = 10.0


class ToolID(Enum):
    VADALOG = "vadalog"
    DLV = "dlv"


class Status(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass()  # frozen=True
class Result:
    name: Optional[str] = None
    command: Optional[List[str]] = None
    time_end2end: Optional[float] = None
    status: Optional[Status] = None
    nb_atoms: Optional[int] = None

    @staticmethod
    def headers() -> str:
        return "name\t" "status\t" "time_end2end\t" "nb_atoms\t" "command"

    def json(self) -> Dict[str, Any]:
        """To json."""
        return dict(
            name=self.name,
            status=self.status.value,
            time_end2end=self.time_end2end,
            nb_atoms=self.nb_atoms,
            command=" ".join(self.command),
        )

    def __str__(self):
        """To string."""
        time_end2end_str = (
            f"{self.time_end2end:10.6f}" if self.time_end2end is not None else "None"
        )
        return (
            f"{self.name}\t"
            f"{self.status.value}\t"
            f"{time_end2end_str}\t"
            f"{self.nb_atoms}\t"
            f"{' '.join(map(str, self.command))}"
        )

    def to_rows(self) -> str:
        """Print results by rows."""
        return (
            f"name={self.name}\n"
            f"status={self.status}\n"
            f"time_end2end={self.time_end2end}\n"
            f"nb_atoms={self.nb_atoms}\n"
            f"command={' '.join(map(str, self.command))}"
        )


def save_data(data: List[Result], output: Path) -> None:
    """Save data to a file."""
    content = ""
    content += Result.headers() + "\n"
    for result in data:
        content += str(result) + "\n"
    output.write_text(content)


def run_tool(args, cwd, timeout):
    start = time.perf_counter()
    timed_out = False
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        preexec_fn=os.setsid,
    )
    stdout, stderr = b"", b""
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        end = time.perf_counter()
    except subprocess.TimeoutExpired:
        end = time.perf_counter()
        proc.terminate()
        with suppress(subprocess.TimeoutExpired):
            stdout, stderr = proc.communicate(timeout=SHUTDOWN_TIMEOUT)
        if proc.poll() is None:
            os.kill(proc.pid, signal.SIGKILL)
            stdout, stderr = proc.communicate(timeout=timeout)
        timed_out = True
    total = end - start
    return proc.returncode, stdout, stderr, total, timed_out


class Tool(ABC):
    """Interface for tools."""

    def __init__(self, binary_path: str):
        """
        Initialize the tool.

        :param binary_path: the binary path
        """
        self._binary_path = binary_path

    @property
    def binary_path(self) -> str:
        """Get the binary path."""
        return self._binary_path

    def run(
        self,
        program: Path,
        datasets: List[Path],
        run_config: Optional[Dict] = None,
        timeout: float = 5.0,
        cwd: Optional[str] = None,
        name: Optional[str] = None,
        working_dir: Optional[str] = None,
    ) -> Result:
        """
        Apply the tool to a file.

        :param program: the program
        :param run_config: the list of datasets
        :param run_config: configuration for the tool run
        :param timeout: the timeout in seconds
        :param cwd: the current working directory
        :param name: the experiment name
        :param working_dir: the working dir
        :return: the planning result
        """
        run_config = ensure_dict(run_config)
        self.start_session()
        args = self.get_cli_args(program, datasets, run_config, working_dir)
        print("Running command: ", " ".join(map(str, args)))
        returncode, stdout, stderr, total, timed_out = run_tool(args, cwd, timeout)
        self.end_session()

        stdout = stdout.decode("utf-8")
        stderr = stderr.decode("utf-8")

        if working_dir is not None:
            (Path(working_dir) / "stdout.txt").write_text(stdout)
            (Path(working_dir) / "stderr.txt").write_text(stderr)

        result = self.collect_statistics(stdout)
        result.name = name
        result.command = args

        # in case time end2end not set by the tool, set from command
        if result.time_end2end is None:
            result.time_end2end = total

        if timed_out:
            result.status = Status.TIMEOUT
        elif result.status is None or returncode != 0:
            result.status = Status.ERROR

        return result

    @abstractmethod
    def collect_statistics(self, output: str) -> Result:
        """
        Collect statistics.

        :param output: the output from where to extract statistics.
        :return: statistics
        """

    @abstractmethod
    def get_cli_args(
        self,
        program: Path,
        datasets: List[Path],
        run_config: Dict,
        working_dir: Optional[str] = None,
    ) -> List[str]:
        """Get CLI arguments."""

    def start_session(self) -> None:
        """Start session."""

    def end_session(self) -> None:
        """End session."""


class ToolSpec:
    """A specification for a particular instance of an object."""

    def __init__(
        self,
        tool_id: ToolID,
        tool_cls: Type[Tool],
        **kwargs: Dict,
    ) -> None:
        """
        Initialize an item specification.

        :param id_: the id associated to this specification
        :param tool_cls: the tool class
        :param kwargs: other custom keyword arguments.
        """
        self.tool_id = tool_id
        self.tool_cls = tool_cls
        self.kwargs = {} if kwargs is None else kwargs

    def make(self, **kwargs: Any) -> Tool:
        """
        Instantiate an instance of the item object with appropriate arguments.

        :param kwargs: the key word arguments
        :return: an item
        """
        _kwargs = self.kwargs.copy()
        _kwargs.update(kwargs)
        tool = self.tool_cls(**_kwargs)
        return tool


class ToolRegistry:
    """Tool registry."""

    def __init__(self):
        """Initialize the registry."""
        self._specs: Dict[ToolID, ToolSpec] = {}

    def register(
        self, tool_id: Union[str, ToolID], tool_cls: Type[Tool], **kwargs: Any
    ):
        """Register a tool."""
        tool_id = ToolID(tool_id)
        self._specs[tool_id] = ToolSpec(tool_id, tool_cls, **kwargs)

    def make(self, tool_id: Union[str, ToolID], **kwargs) -> Tool:
        """
        Make the tool.

        :param tool_id: the tool ID
        :param kwargs: the overrides for keyword arguments
        :return: the tool instance
        """
        tool_id = ToolID(tool_id)
        if tool_id not in self._specs:
            raise ValueError(f"tool id '{tool_id}' not configured")
        tool_spec = self._specs[ToolID(tool_id)]
        return tool_spec.make(**kwargs)
