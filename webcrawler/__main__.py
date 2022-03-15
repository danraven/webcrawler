from webcrawler.runner import Runner
from webcrawler.config import Config
import argparse


def run():
    parser = argparse.ArgumentParser(description="Basic website crawler/scraper")
    parser.add_argument(
        "config",
        metavar="path/to/config.toml",
        nargs=1,
        help="Path to the TOML config for the runner",
    )
    args = parser.parse_args()
    runner = Runner.from_config(Config.from_toml(args.config))
    try:
        runner.run()
    except KeyboardInterrupt:
        runner.logger.info("Received interrupt signal, closing.")


if __name__ == "__main__":
    run()
