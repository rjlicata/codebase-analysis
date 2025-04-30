from codebase_analysis import Orchestrator


def main(config_path: str, init: bool) -> None:
    """runs the orchestrator to add data to the database"""
    db_handler = Orchestrator(config_path=config_path, init=init)
    if init:
        db_handler.add_data()
    db_handler.query("Is there a way to send a message to an LLM?")


if __name__ == "__main__":
    main(config_path="/workspace/data/base_config.yml", init=True)
