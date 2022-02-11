import re
from pathlib import Path
from typing import List


def max_digits(dataset_partition_filenames):
    return max(
        map(
            lambda name: len(Path(name).stem.split("_")[1]), dataset_partition_filenames
        )
    )


def get_normalized_integer(number: int, max_nb_digits: int) -> str:
    return ("{:0" + str(max_nb_digits) + "d}").format(number)


def from_str_to_int_with_label(arg: str) -> int:
    pattern = r"([0-9]+)(m|k)?"
    match = re.match(pattern, arg)
    if match is None:
        raise ValueError(f"pattern '{pattern}' not recognized with input: '{arg}'")
    number = match.group(1)
    power_str = match.group(2)
    power = 6 if power_str == "m" else 3 if power_str == "k" else 0
    return int(number) * 10**power


def quote_csv_line(line: str):
    tokens = line.split(",")
    new_tokens = []
    for token in tokens:
        # if already double-quoted, don't quote
        if token and token[0] == '"' and token[-1] == '"':
            assert '"' not in token[1:-1], "quotes are not allowed"
            new_tokens.append(token)
        else:
            assert '"' not in token, "quotes are not allowed"
            new_tokens.append(f'"{token}"')
    return ",".join(new_tokens)


def quote_csv_file(input_content: str) -> str:
    return "\n".join(map(quote_csv_line, input_content.splitlines(keepends=False)))


def transform_dataset_file(input_file: Path, output_file: Path, predicate_name: str):
    lines = input_file.read_text().splitlines(keepends=False)
    atoms = map(lambda line: f"{predicate_name}(" + quote_csv_line(line) + ").", lines)
    output_file.write_text("\n".join(atoms))


def normalize_name(file_name: str, min_digits: int):
    dataset_name, nb_rows = Path(file_name).stem.split("_")
    new_nb_rows = (min_digits - len(nb_rows)) * "0" + nb_rows
    return f"{dataset_name}_{new_nb_rows}"


def transform_dataset_file_with_header(
    header: str, lines: List[str], output_file: Path, predicate_name: str
):
    atoms = map(lambda line: f"{predicate_name}(" + quote_csv_line(line) + ").", lines)
    output_file.write_text((header + "\n" if header else "") + "\n".join(atoms))


def write_lines_for_vadalog(header: str, lines: List[str], output_file: Path, *_):
    output_file.write_text(header + "\n" + "\n".join(lines))


def normalize(lines: List[str], nb_https: int):
    assert nb_https > 0
    new_lines = []
    for line in lines:
        match = re.search(",".join(["(http.*)"] * nb_https), line)
        groups = [match.group(i + 1) for i in range(nb_https)]
        normalized_groups = [group.replace(",", "_") for group in groups]
        new_line = ",".join(normalized_groups)
        new_lines.append(new_line)
    return new_lines


def normalize_person_dataset(lines: List[str]):
    new_lines = []
    for line in lines:
        match = re.search("(.*),.*,.*,.*,.*", line)
        new_line = match.group(1)
        new_lines.append(new_line.replace(",", "_"))
    return new_lines


def get_nb_columns_from_csv(input_file: Path) -> int:
    return len(input_file.read_text().split("\n", maxsplit=1)[0].split(","))
