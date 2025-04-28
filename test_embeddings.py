import yaml
from codebase_analysis.llm import Embeddings


def load_config(path: str) -> dict:
    """loads the config file

    :param path: path to the config file
    :type path: str
    :return: loaded config
    :rtype: dict
    """
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    return config


if __name__ == "__main__":
    path = "/workspace/data/base_config.yml"
    config = load_config(path)

    emb = Embeddings(config["embeddings"])
    text = "This is a test"
    embedding = emb.generate(text)
    print(embedding)
    print(type(embedding))
