import re
from typing import Dict, List


def find_funcs(path: str = None, text: str = None, indent: int = 0) -> Dict[str, List[str]]:
    """find all functions in a Python file or chunk of text (preloaded file)

    :param path: path to the file, defaults to None
    :type path: str, optional
    :param text: text to search in, defaults to None
    :type text: str, optional
    :param inedent: indentation level, defaults to 0
    :type inedent: int, optional
    :return: list of functions
    :rtype: Dict[str, List[str]]
    """
    assert (path is not None) or (text is not None)
    spaces = " " * 4 * indent
    if text is None:
        with open(path, "r") as f:
            lines = f.readlines()
    else:
        lines = text.split("\n")
        lines = [line + "\n" for line in lines]
    functions = {}
    in_func = False
    func_name = ""
    current_func = []
    for line in lines:
        if line.startswith(f"{spaces}def "):
            if len(current_func) > 0:
                current_func = [item for item in current_func if item != "\n"]
                functions[func_name] = "".join(current_func)
                current_func = []
            func_name = line.split("def ")[1].split("(")[0]
            current_func.append(line)
            in_func = True
            continue
        if in_func:
            if (len(line) > 0) and (line[0] != " ") and (len(re.findall(r"\w", line)) > 0):
                current_func = [item for item in current_func if item != "\n"]
                functions[func_name] = "".join(current_func)
                current_func = []
                in_func = False
            else:
                current_func.append(line)
    if in_func:
        current_func = [item for item in current_func if item != "\n"]
        functions[func_name] = "".join(current_func)
    return functions


def find_classes(path: str) -> Dict[str, List[str]]:
    """find all classes in a Python file

    :param path: path to the file
    :type path: str
    :return: dictionary containing whole class in addition to its methods
    :rtype: Dict[str, List[str]]
    """
    with open(path, "r") as f:
        lines = f.readlines()
    classes = {}
    in_class = False
    class_name = ""
    current_class = []
    for line in lines:
        if line.startswith(f"class "):
            if len(current_class) > 0:
                current_class = [item for item in current_class if item != "\n"]
                classes[class_name] = {"text": "".join(current_class)}
                current_class = []
            class_name = line.split("class ")[1].split(":")[0].split("(")[0]
            current_class.append(line)
            in_class = True
            continue
        if in_class:
            if (line[0] != " ") and (len(re.findall(r"\w", line)) > 0):
                current_class = [item for item in current_class if item != "\n"]
                classes[class_name] = {"text": "".join(current_class)}
                current_class = []
                in_class = False
            else:
                current_class.append(line)
    if in_class:
        current_class = [item for item in current_class if item != "\n"]
        classes[class_name] = {"text": "".join(current_class)}
    for key in classes:
        classes[key]["methods"] = find_funcs(text=classes[key]["text"], indent=1)
    return classes


if __name__ == "__main__":
    # CLASSES
    path = "/workspace/src/codebase_analysis/llm/model.py"
    classes = find_classes(path)
    for k, v in classes.items():
        print(f"======{k}======")
        print(v["text"])
        for k1, v1 in v["methods"].items():
            print(k1)
            print(v1)
            print("--" * 20)
    # FUNCTIONS
    # path = "/workspace/src/codebase_analysis/file_utils/read.py"
    # functions = find_funcs(path)
    # print(f"There are {len(functions)} function(s)")
    # for k, v in functions.items():
    #     print(k)
    #     print(v)
    #     print("--" * 20)
