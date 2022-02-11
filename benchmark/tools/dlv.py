import re
from pathlib import Path
from typing import Dict, List, Optional

from benchmark import ROOT_DIR
from benchmark.tools.core import Result, Status, Tool

DEFAULT_DLV_ROOT = ROOT_DIR / "third_party" / "TOCL_dlvEx"
DLV_WRAPPER_PATH = ROOT_DIR / "bin" / "dlv-wrapper"
DEFAULT_DLV_BINARY_PATH = DEFAULT_DLV_ROOT / "dlvExists"


class DlvTool(Tool):
    """Implement the DLV tool wrapper."""

    NAME = "DLV^E"

    def collect_statistics(self, output: str) -> Result:
        qa_time = re.search("Query Answering Time", output)
        status = Status.SUCCESS if qa_time else Status.ERROR

        result = re.search(
            "for further information\.\)\n(.*)\nQuery Answering",
            output,
            re.DOTALL | re.MULTILINE,
        )
        if result is not None:
            atoms_string = result.group(1)
            atoms = atoms_string.splitlines()
            nb_atoms = len(atoms)
        else:
            nb_atoms = None
        return Result(status=status, nb_atoms=nb_atoms)

    def get_cli_args(
        self,
        program: Path,
        datasets: List[Path],
        run_config: Dict,
        working_dir: Optional[str] = None,
    ) -> List[str]:
        args = [self.binary_path, "--program", program]
        assert len(datasets) > 0
        args += ["--dataset", *map(str, datasets)]
        if working_dir is not None:
            args += ["--working-dir", str(Path(working_dir).absolute())]
        return args
