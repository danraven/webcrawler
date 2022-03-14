from webcrawler.runner import Runner
from webcrawler.config import Config


def run():
    runner = Runner.from_config(Config.from_toml('./oda_products.toml'))
    try:
        runner.run()
    except KeyboardInterrupt:
        runner.logger.info('Received interrupt signal, closing.')


if __name__ == '__main__':
    run()
