import yaml
from typing import Any, Dict, List, Tuple

import numpy as np

from codebase_analysis.db_utils import dbHandler
from codebase_analysis.file_utils import find_classes, find_funcs, get_all_files
from codebase_analysis.llm import Embeddings, ModelHandler
from codebase_analysis.llm.prompts import (
    CLASS_SUMMARIZATION_PROMPT,
    FUNCTION_SUMMARIZATION_PROMPT,
    METHOD_SUMMARIZATION_PROMPT,
    QA_SYSTEM_PROMPT,
)


class Orchestrator:
    """Orchestrator class to handle the database and model interactions"""

    def __init__(
        self, config_path: str, repo_path: str = None, max_context: int = 5, init: bool = True
    ):
        """initializes Orchestrator

        :param config_path: path to the config file
        :type config_path: str
        :param repo_path: override for the repo path, defaults to None
        :type repo_path: str, optional
        :param max_context: maximum number of summaries to provide the model for answering, defaults to 5
        :type max_context: int, optional
        :param init: whether to initialize the database, defaults to True
        :type init: bool, optional
        """
        self._config = self._load_config(config_path)
        self._max_context = max_context
        self._model_handler = ModelHandler(
            self._config["llm"], system_message=FUNCTION_SUMMARIZATION_PROMPT
        )
        self._embedder = Embeddings(self._config["embeddings"])
        self._db = dbHandler(
            self._config["postgres"],
            embedding_dim=self._config["embeddings"]["embedding_dim"],
            init=init,
        )
        if repo_path is not None:
            self._config["codebase"]["path"] = repo_path

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
        """extract all functions, classes, and methods from the repo and add them to the database"""
        codebase = self._breakdown_repo()
        for key in codebase:
            codebase[key] = self._add_summaries(codebase[key])
            self._db.add_file(key, codebase[key])

    def _order_context(self, results: Dict[str, Dict[str, Any]]) -> List[str]:
        """orders the context to be used in the prompt

        :param results: results from the database
        :type results: Dict[str, Dict[str, Any]]
        :return: ordered keys
        :rtype: List[str]
        """
        keys, dist = [], []
        for k, v in results.items():
            keys.append(k)
            dist.append(v["cos_dist"])
        ordered_keys = [keys[int(d)] for d in np.argsort(dist)]
        return ordered_keys

    def _create_context_string(self, results: Dict[str, Dict[str, Any]]) -> str:
        """creates a context string from the results

        :param results: results from the database
        :type results: Dict[str, Dict[str, Any]]
        :return: context string
        :rtype: str
        """
        ordered_keys = self._order_context(results)
        context = ""
        for k in ordered_keys[: self._max_context]:
            context += f"[{k}]: Name - {results[k]['name']}, Summary - {results[k]['summary']}\n\n"
        return context

    def _get_filepath(self, result: Dict[str, Any]) -> Tuple[str, str]:
        """gets the file path (and potentially parent class name) of the result

        :param result: result from the database
        :type result: Dict[str, Any]
        :return: file path
        :rtype: Tuple[str, str]
        """
        if result["type"] != "methods":
            query = f"""SELECT files.path
            FROM files
            INNER JOIN {result['type']} ON {result['type']}.file_id = files.id
            WHERE {result['type']}.id = {result['id']};
            """
            output = self._db.run_basic_query(query)
            return output[0][0], None
        else:
            query = f"""SELECT files.path, classes.name
            FROM files
            INNER JOIN classes ON classes.file_id = files.id
            INNER JOIN methods ON methods.class_id = classes.id
            WHERE methods.id = {result['id']};
            """
            output = self._db.run_basic_query(query)
            return output[0][0], output[0][1]

    def _reformat(self, response: str, results: Dict[str, Dict[str, Any]]) -> str:
        """reformats the response to clean up the in-text citations and provide the path to the code

        :param response: response
        :type response: str
        :param results: results from the database
        :type results: Dict[str, Dict[str, Any]]
        :return: reformatted response
        :rtype: str
        """
        citation_counter = 1
        citation_dict = {}
        for k in results:
            if k in response:
                path, class_name = self._get_filepath(results[k])
                response = response.replace(k, str(citation_counter))
                citation_dict[citation_counter] = {
                    "path": path,
                    "class_name": class_name,
                    "name": results[k]["name"],
                    "type": results[k]["type"],
                }
                citation_counter += 1
        if len(citation_dict) > 0:
            response += "\n\nREFERENCES:\n"
            for k in citation_dict:
                path = citation_dict[k]["path"].replace("/workspace/tmp/", "")
                class_name = citation_dict[k]["class_name"]
                name = citation_dict[k]["name"]
                response += f"[{k}]: {name} - (path: {path})\n"
                if citation_dict[k]["type"] == "methods":
                    response = response.replace(
                        f"[{k}]: {name}",
                        f"[{k}]: class: {class_name}.{name}",
                    )
            response = response[:-1]
        for i in range(self._max_context):
            response = response.replace(f"([{i+1}])", f"[{i+1}]")
        return response

    def query(self, query: str) -> str:
        """queries the database for the given query

        :param query: user question
        :type query: str
        :return: response from the model
        :rtype: str
        """
        template = "CONTEXT:\n{context}\nQUESTION: {query}\nANSWER:\n"
        vec = self._embedder.generate(query)
        results = self._db.run_similarity(vec)
        context = self._create_context_string(results)
        response = self._model_handler.invoke(
            template.format(context=context, query=query),
            sys_msg=QA_SYSTEM_PROMPT,
        )
        self._model_handler.clear_messages()
        response = self._reformat(response, results)
        return response


if __name__ == "__main__":
    db_handler = Orchestrator(config_path="/workspace/data/base_config.yml")
    codebase = db_handler.add_data()
    print()
