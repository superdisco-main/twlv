import argparse

AZURE_DEPLOYMENTS = {
    "planner": {"deployment_name": "gpt-4o", "model_version": "2024-05-13"},
    "supervisor": {"deployment_name": "gpt-4o", "model_version": "2024-05-13"},
    "worker": {"deployment_name": "gpt-4o", "model_version": "2024-07-18"},
    "ask_human": {"deployment_name": "gpt-4o", "model_version": "2024-07-18"},
}

OPENAI_MODELS = {
    "planner": "gpt-4o",
    "supervisor": "gpt-4o",
    "worker": "gpt-4o",
    "ask_human": "gpt-4o",
    "reflect": "gpt-4o",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Jockey Video Search")
    parser.add_argument("-s", "--server", action="store_true", help="Run in server mode")
    args, unknown = parser.parse_known_args()

    # Handle the case where someone uses the old "server" argument
    if unknown and unknown[0] == "server":
        args.server = True

    return args


args = parse_args()
