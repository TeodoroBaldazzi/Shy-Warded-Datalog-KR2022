#!/usr/bin/env python3
from pathlib import Path
from typing import Callable, Dict

from benchmark.tools import ToolID
from benchmark.utils.base import remove_dir_or_fail
from scripts import ROOT_DIR
from scripts.utils.base import (
    get_normalized_integer,
    normalize,
    normalize_person_dataset,
    transform_dataset_file_with_header,
    write_lines_for_vadalog,
)

DBPEDIA_DATASET_DIR = ROOT_DIR / Path(
    "third_party/original_datasets/dbpedia"
)


FULL_PERSON_DATASET_PATH = DBPEDIA_DATASET_DIR / "persons_1m.csv"
COMPANIES_KP_DATASET_PATH = DBPEDIA_DATASET_DIR / "dbpedia_companies_kp.csv"
CONTROL_DATASET_PATH = DBPEDIA_DATASET_DIR / "dbpedia_company_control.csv"

SIZES = [1000, 10000, 100000, 500000, 1000000]


dataset_handlers: Dict[ToolID, Callable] = {
    ToolID.VADALOG: write_lines_for_vadalog,
    ToolID.DLV: transform_dataset_file_with_header,
}


def generate_psc(output_dir: Path, force: bool):
    dataset_name = "psc"
    output_dataset_dir = output_dir / dataset_name
    remove_dir_or_fail(output_dataset_dir, force)
    output_dataset_dir.mkdir(parents=True)

    dataset_max_digits = len(str(SIZES[-1]))
    person_dataset_lines = FULL_PERSON_DATASET_PATH.read_text().splitlines(
        keepends=False
    )
    person_dataset_header, person_dataset_rows = (
        person_dataset_lines[0],
        person_dataset_lines[3:],
    )
    person_dataset_header = person_dataset_header.split(",")[0]
    person_dataset_rows = normalize_person_dataset(person_dataset_rows)

    control_lines = CONTROL_DATASET_PATH.read_text().splitlines(keepends=False)
    control_header, control_rows = "company_1,company_2", normalize(
        control_lines, nb_https=2
    )
    kp_lines = COMPANIES_KP_DATASET_PATH.read_text().splitlines(keepends=False)
    kp_header, kp_rows = kp_lines[0], normalize(kp_lines[1:], nb_https=2)

    for tool in ToolID:
        dataset_handler = dataset_handlers[tool]
        tool_output_dataset_dir = output_dataset_dir / tool.value
        tool_output_dataset_dir.mkdir()

        for size in SIZES:
            # copy persons
            normalized_partition_name = get_normalized_integer(size, dataset_max_digits)
            tool_output_partition_dir = (
                tool_output_dataset_dir / normalized_partition_name
            )
            tool_output_partition_dir.mkdir()

            dataset_partition = person_dataset_rows[:size]
            output_dataset_file = tool_output_partition_dir / "person.data"
            dataset_handler(
                "",
                dataset_partition,
                output_dataset_file,
                "person",
            )

            # copy company_control
            dataset_handler(
                "",
                control_rows,
                tool_output_partition_dir / "control.data",
                "control",
            )
            # copy companies_kp
            dataset_handler(
                "",
                kp_rows,
                tool_output_partition_dir / "keyPerson.data",
                "keyPerson",
            )
