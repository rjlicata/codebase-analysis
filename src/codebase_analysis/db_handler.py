import yaml
from typing import Any, Dict

from codebase_analysis.file_utils import find_classes, find_funcs, get_all_files
from codebase_analysis.llm import ModelHandler


class DBHandler:
    def __init__(self, config_path: str):
        """initializes DBHandler

        :param config_path: path to the config file
        :type config_path: str
        """
        self._config = self._load_config(config_path)
        self._model_handler = ModelHandler(self._config["model_config"])

    def _load_config(self, path: str) -> Dict[str, Any]:
        """loads the config file

        :param path: path to the config file
        :type path: str
        :return: loaded config
        :rtype: Dict[str, Any]
        """
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        return config
