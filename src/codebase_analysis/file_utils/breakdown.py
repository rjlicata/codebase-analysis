from glob import glob
from typing import List


def get_all_files(path: str, file_type: str = ".py") -> List[str]:
    """returns all files in a directory with a specific file type

    :param path: path to the directory
    :type path: str
    :param file_type: file extension to search for, defaults to ".py"
    :type file_type: str, optional
    :return: list of filepaths in the directory
    :rtype: List[str]
    """
    return glob(f"{path}/**/*{file_type}", recursive=True)


if __name__ == "__main__":
    path = "/coding-projects/llm-sheet-analysis"
    file_type = ".py"
    files = get_all_files(path, file_type)
    print(files)
