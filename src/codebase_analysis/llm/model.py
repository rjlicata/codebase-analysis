from typing import Any, Dict, List

from openai import OpenAI

from codebase_analysis.llm.prompts import BASIC_SYSTEM_MESSAGE


class ModelHandler:
    """handles basic communication with the LLM model endpoint; works for Ollama, HuggingFace TGI, and vLLM models

    Ollama: model_name is the Ollama name for the model
    HuggingFace TGI: model_name is the "tgi"
    vLLM: model_name is the mounted path to the model

    For all these options, the endpoint_url should be "http://localhost:<port>/v1"
    Ollama defaults to port 11434, but you would manually define it when hosting a model on HuggingFace TGI or vLLM

    This is all handled in the base_config.yml file
    """

    def __init__(
        self,
        config: Dict[str, Any],
        system_message: str = BASIC_SYSTEM_MESSAGE,
        temperature: float = 0.7,
    ):
        """initializes ModelHandler

        :param config: model config
        :type config: Dict[str, Any]
        :param system_message: system message for the LLM, defaults to BASIC_SYSTEM_MESSAGE
        :type system_message: str, optional
        :param temperature: generation temperature for the model, defaults to 0.7
        :type temperature: float, optional
        """
        if "/v1" not in config["endpoint_url"]:
            config["endpoint_url"] += "/v1"
        self._client = OpenAI(
            base_url=config["endpoint_url"],
            api_key="EMPTY",
        )
        self._model_name = config["model_name"]
        self._system_message = system_message
        self._temperature = temperature
        self.clear_messages()

    def clear_messages(self) -> None:
        """resets messages with only system message"""
        self._messages = [
            {
                "role": "system",
                "content": self._system_message,
            },
        ]

    def invoke(self, user_message: str, sys_msg: str = None) -> str:
        """handles the message list and invokes the LLM

        :param user_message: user query
        :type user_message: str
        :param sys_msg: user override to system message, defaults to None
        :type sys_msg: str, optional
        :return: model response
        :rtype: str
        """
        if sys_msg is not None:
            self._messages[0]["content"] = sys_msg
        self._messages.append(
            {
                "role": "user",
                "content": user_message,
            },
        )
        response = (
            self._client.chat.completions.create(
                messages=self._messages,
                model=self._model_name,
                temperature=self._temperature,
            )
            .choices[0]
            .message.content
        )
        self._messages.append(
            {
                "role": "assistant",
                "content": response,
            },
        )
        return response


class Embeddings:
    """handles embedding generation TEI endpoint"""

    def __init__(self, config: Dict[str, Any]):
        """initializes Embeddings

        :param config: embedding model config
        :type config: Dict[str, Any]
        """
        if "/v1" not in config["endpoint_url"]:
            config["endpoint_url"] += "/v1"
        self._client = OpenAI(
            base_url=config["endpoint_url"],
            api_key="EMPTY",
        )
        self._model_name = config.get("model_name", "TEI")

    def generate(self, text: str) -> List[str]:
        """generate embeddings from the TEI endpoint

        :param text: text to vectorize
        :type text: str
        :return: generated embedding vector
        :rtype: List[str]
        """
        response = (
            self._client.embeddings.create(
                input=text,
                model=self._model_name,
            )
            .data[0]
            .embedding
        )
        return response
