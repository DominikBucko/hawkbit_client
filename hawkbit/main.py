import json
import yaml
from config import config
import logging
import os
from polling_client import poll


def main():
    # Set up logging to Systemd stderr
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

    with open("../config.yaml") as configFile:
        try:
            tmp = yaml.safe_load(configFile)
        except yaml.YAMLError:
            logging.error("Invalid yaml file.")
            exit(1)
        config.__dict__ = tmp

    with open("../deviceConfig.json") as deviceConfigFile:
        try:
            device_config = json.load(deviceConfigFile)
        except json.JSONDecodeError:
            logging.error("Couldn't load configData")
            exit(1)
        config.__dict__["deviceConfig"] = device_config


    poll()


if __name__ == '__main__':
    main()
