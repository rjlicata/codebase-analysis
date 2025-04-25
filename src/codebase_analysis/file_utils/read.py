import os
import re
from string import ascii_letters


def find_funcs(path: str) -> None:
    """find all functions in a Python file

    :param path: path to the file
    :type path: str
    """
    with open(path, "r") as f:
        lines = f.readlines()
    functions = []
    in_func = False
    current_func = []
    for line in lines:
        if line.startswith("def "):
            if len(current_func) > 0:
                current_func = [item for item in current_func if item != "\n"]
                functions.append("".join(current_func))
                current_func = []
            current_func.append(line)
            in_func = True
            continue
        if in_func:
            if (line[0] != " ") and (len(re.findall(r"\w", line)) > 0):
                current_func = [item for item in current_func if item != "\n"]
                functions.append("".join(current_func))
                current_func = []
                in_func = False
            else:
                current_func.append(line)
    return functions


if __name__ == "__main__":
    path = "/workspace/src/codebase_analysis/file_utils/read.py"
    functions = find_funcs(path)
    print(f"There are {len(functions)} function(s)")
    for func in functions:
        print(func)
        print("--" * 20)
