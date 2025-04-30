import yaml
from typing import Any, Dict, List, Tuple

from codebase_analysis.db_utils import dbHandler
from codebase_analysis.file_utils import find_classes, find_funcs, get_all_files
from codebase_analysis.llm import Embeddings, ModelHandler
from codebase_analysis.llm.prompts import (
    CLASS_SUMMARIZATION_PROMPT,
    FUNCTION_SUMMARIZATION_PROMPT,
    METHOD_SUMMARIZATION_PROMPT,
)


class Orchestrator:
    """Orchestrator class to handle the database and model interactions"""

    def __init__(self, config_path: str, init: bool = True):
        """initializes Orchestrator

        :param config_path: path to the config file
        :type config_path: str
        :param init: whether to initialize the database, defaults to True
        :type init: bool, optional
        """
        self._config = self._load_config(config_path)
        self._model_handler = ModelHandler(
            self._config["llm"], system_message=FUNCTION_SUMMARIZATION_PROMPT
        )
        self._embedder = Embeddings(self._config["embeddings"])
        self._db = dbHandler(self._config["postgres"], embedding_dim=self._config["embeddings"]["embedding_dim"], init=init)

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

    def _breakdown_repo(self) -> None:
        files = get_all_files(
            path=self._config["codebase"]["path"],
            file_type=".py",
        )
        codebase = {}
        for file in files:
            codebase[file] = {}
            codebase[file]["classes"] = find_classes(file)
            codebase[file]["functions"] = find_funcs(file)
        return codebase

    def _get_summary_and_embedding(self, code: str, sys_msg: str) -> Tuple[str, List[float]]:
        """gets the summary and embedding of the code

        :param code: code to get the summary and embedding of
        :type code: str
        :return: summary and embedding
        :rtype: Tuple[str, List[float]]
        """
        template = "INPUT:\n```\n{code}\n```\nSUMMARY:\n"
        summary = self._model_handler.invoke(template.format(code=code), sys_msg=sys_msg)
        self._model_handler.clear_messages()
        embedding = self._embedder.generate(summary)
        return summary, embedding

    def _add_summaries(self, filedict: Dict[str, str]) -> Dict[str, str]:
        """adds summaries to the functions and classes in the filedict

        :param filedict: dictionary of files
        :type filedict: Dict[str, str]
        :return: dictionary of files with summaries
        :rtype: Dict[str, str]
        """
        for funcname in filedict["functions"]:
            code = filedict["functions"][funcname]["text"]
            summary, embedding = self._get_summary_and_embedding(
                code, sys_msg=FUNCTION_SUMMARIZATION_PROMPT
            )
            filedict["functions"][funcname]["summary"] = summary
            filedict["functions"][funcname]["embedding"] = embedding
        for classname in filedict["classes"]:
            code = filedict["classes"][classname]["text"]
            summary, embedding = self._get_summary_and_embedding(
                code, sys_msg=CLASS_SUMMARIZATION_PROMPT
            )
            filedict["classes"][classname]["summary"] = summary
            filedict["classes"][classname]["embedding"] = embedding
            for methodname in filedict["classes"][classname]["methods"]:
                code = filedict["classes"][classname]["methods"][methodname]["text"]
                summary, embedding = self._get_summary_and_embedding(
                    code, sys_msg=METHOD_SUMMARIZATION_PROMPT
                )
                filedict["classes"][classname]["methods"][methodname]["summary"] = summary
                filedict["classes"][classname]["methods"][methodname]["embedding"] = embedding
        return filedict

    def add_data(self) -> None:
        codebase = self._breakdown_repo()
        for key in codebase:
            codebase[key] = self._add_summaries(codebase[key])
            self._db.add_file(key, codebase[key])
    
    def query(self, query: str) -> None:
        """queries the database for the given query

        :param query: user question
        :type query: str
        """
        vec = self._embedder.generate(query)
        results = self._db.run_similarity(vec)
        
        return results


if __name__ == "__main__":
    db_handler = Orchestrator(config_path="/workspace/data/base_config.yml")
    codebase = db_handler.add_data()
    print()
