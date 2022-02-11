#!/usr/bin/env python3
from pathlib import Path
from typing import Callable, Dict

from benchmark.tools import ToolID
from benchmark.utils.base import remove_dir_or_fail
from scripts import ROOT_DIR
from scripts.utils.base import (
    from_str_to_int_with_label,
    get_nb_columns_from_csv,
    get_normalized_integer,
    transform_dataset_file_with_header,
    write_lines_for_vadalog,
)

DOCTORS_DATASET_DIR = ROOT_DIR / Path("third_party/original_datasets/doctors")


dataset_handlers: Dict[ToolID, Callable] = {
    ToolID.VADALOG: write_lines_for_vadalog,
    ToolID.DLV: transform_dataset_file_with_header,
}


def generate_doctors(input_dir: Path, output_dir: Path, force: bool):
    dataset_name = input_dir.name
    output_dataset_dir = output_dir / dataset_name
    remove_dir_or_fail(output_dataset_dir, force)
    output_dataset_dir.mkdir(parents=True)

    for tool in ToolID:
        dataset_handler = dataset_handlers[tool]
        tool_output_dataset_dir = output_dataset_dir / tool.value
        tool_output_dataset_dir.mkdir()

        # get max digits number
        sizes = map(
            lambda p: from_str_to_int_with_label(p.name), DOCTORS_DATASET_DIR.iterdir()
        )
        max_nb_digits = len(str(max(sizes)))

        for subdir in DOCTORS_DATASET_DIR.iterdir():
            partition_name = subdir.name
            full_integer = from_str_to_int_with_label(partition_name)
            normalized_partition_name = get_normalized_integer(
                full_integer, max_nb_digits
            )
            output_dataset_subdir = tool_output_dataset_dir / normalized_partition_name
            output_dataset_subdir.mkdir(parents=True)
            for dataset_file in subdir.iterdir():
                output_dataset_file = output_dataset_subdir / (
                    dataset_file.stem + ".data"
                )
                dataset_handler(
                    "",
                    dataset_file.read_text().splitlines(keepends=False),
                    output_dataset_file,
                    dataset_file.stem,
                )
