import re


def process_line_for_dlv(line: str) -> str:
    check_output = re.match('@output\("(.*)"\)', line)
    if check_output is not None:
        # to be processed later
        return line

    head, body = line.split(":-")
    head = head.strip()
    body = body.strip()
    variable_regex = " *[a-zA-Z0-9_]+\((.*)\)"

    head_variables_string = re.search(variable_regex, head).group(1)
    head_variables_string = re.sub(" +", "", head_variables_string)
    head_variables = set(head_variables_string.split(","))

    body_variables = set()
    for body_atom in re.findall(" *[a-zA-Z0-9_]+\(.*?\)", body):
        body_atom = body_atom.strip()
        body_atom_variables_string = re.search(variable_regex, body_atom).group(1)
        body_atom_variables_string = re.sub(" +", "", body_atom_variables_string)
        body_atom_variables = set(body_atom_variables_string.split(","))
        body_variables.update(body_atom_variables)

    existentially_quantified_vars = head_variables.difference(body_variables)

    if existentially_quantified_vars:
        dlv_exist_prefix = (
            f"#exists{{{','.join(sorted(existentially_quantified_vars))}}}"
        )
        line = dlv_exist_prefix + line
    return line


def process_program_for_vadalog(input_file: str) -> str:
    input_file = re.sub("%.*\n", "", input_file)
    input_file = re.sub("@(bind|mapping|input).*\n", "", input_file)
    return input_file


def process_program_for_dlv(input_file: str) -> str:
    input_file = re.sub("%.*\n", "", input_file)
    input_file = re.sub("@(bind|mapping|input).*\n", "", input_file)

    lines = input_file.splitlines(keepends=False)
    lines = [line for line in lines if line.strip()]
    new_lines = map(process_line_for_dlv, lines)
    output = "\n".join(new_lines)

    # find output predicates
    output_statements = sorted(set(re.findall('@output\("(.*)"\)', output)))
    if len(output_statements) == 0:
        return output

    assert len(output_statements) == 1
    predicate_name = output_statements[0]
    # find output predicate in the program
    finditer = re.finditer(f" *(#exists{{(.*?)}})? *{predicate_name}\((.*?)\)", output)
    output_match = next(finditer)
    _, exist_variables_string, variables_string = output_match.groups()
    variables = variables_string.split(",")
    nb_variables = len(variables)
    id_to_new_var = [f"X{i}" for i in range(nb_variables)]
    new_variables_string = ",".join(id_to_new_var)
    new_exist_clause = ""
    if exist_variables_string:
        exist_vars = exist_variables_string.split(",")
        exist_positions = [i for i in range(nb_variables) if variables[i] in exist_vars]
        new_exist_variable_string = ",".join(
            map(lambda vid: id_to_new_var[vid], exist_positions)
        )
        new_exist_clause = f"#exists{{{new_exist_variable_string}}}"
    dlv_query = f"{new_exist_clause}{predicate_name}({new_variables_string})?"
    # remove old output statement
    output = re.sub("@.*\n?", "", output)
    # add new line
    output += "\n" + dlv_query

    return output
