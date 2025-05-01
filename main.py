from codebase_analysis import Orchestrator


def main(config_path: str, init: bool) -> None:
    """runs the orchestrator to add data to the database"""
    db_handler = Orchestrator(config_path=config_path, init=init)
    if init:
        db_handler.add_data()
    while True:
        user_input = input("Enter a query: ")
        print("-" * 50)
        if user_input.lower() == "exit":
            break
        response = db_handler.query(user_input)
        print(response)
        print("-" * 50)


if __name__ == "__main__":
    main(config_path="/workspace/data/base_config.yml", init=True)
