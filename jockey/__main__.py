import asyncio
from jockey.cli import run_jockey_terminal, run_jockey_server
from jockey.util import preflight_checks
from jockey.model_config import args


def main():
    # preflight_checks()

    # clear event_log.txt
    with open("event_log.txt", "w") as f:
        f.write("")

    # run server
    if args.server:
        run_jockey_server()

    # run terminal
    else:
        asyncio.run(run_jockey_terminal())


if __name__ == "__main__":
    main()
