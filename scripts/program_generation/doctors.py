import re
import shutil
from pathlib import Path
from typing import Callable, Dict

from benchmark.tools import ToolID
from scripts import ROOT_DIR
from scripts.utils.base import from_str_to_int_with_label, get_normalized_integer
from scripts.utils.translate import process_program_for_dlv, process_program_for_vadalog

DOCTORS_DIR = ROOT_DIR / Path("third_party/original_programs/doctors")


program_handler: Dict[ToolID, Callable] = {
    ToolID.VADALOG: process_program_for_vadalog,
    ToolID.DLV: process_program_for_dlv,
}

partition_names = [
    "1m",
    "10k",
    "100k",
    "500k",
]


def generate_doctors(input_dir: Path, output_dir: Path, force: bool):
    # remove all previous programs
    for old_program_dir in output_dir.glob(input_dir.name + "-q*"):
        shutil.rmtree(old_program_dir, ignore_errors=True)

    # get max digits number
    sizes = map(lambda p: from_str_to_int_with_label(p), partition_names)
    max_nb_digits = len(str(max(sizes)))
    for partition_name in partition_names:
        size = from_str_to_int_with_label(partition_name)
        for program in sorted(input_dir.glob(f"program_{partition_name}q*.vada")):
            query_name = re.search("q[0-9]+", program.name).group(0)
            current_output_dir = output_dir / f"{input_dir.name}-{query_name}"
            current_output_dir.mkdir(exist_ok=True)
            current_partition_output_dir = current_output_dir / get_normalized_integer(
                size, max_nb_digits
            )
            current_partition_output_dir.mkdir()
            for tool in ToolID:
                output_content = program_handler[tool](program.read_text())
                output_file = current_partition_output_dir / (tool.value + ".txt")
                output_file.write_text(output_content)
