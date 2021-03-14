import json
import yaml
from config import config
import logging
import os
from polling_client import poll
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="config.yaml file location")
    parser.add_argument("-d", "--device-config", help="location of device config json file")

    args = parser.parse_args()

    # Set up logging to Systemd stderr
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

    try:
        with open(args.config) as configFile:
            try:
                tmp = yaml.safe_load(configFile)
            except yaml.YAMLError:
                logging.error("Invalid yaml file.")
                exit(1)
            config.__dict__ = tmp
    except FileNotFoundError:
        logging.error("Invalid path to config.yaml file. Exitting.")
        exit(1)

    try:
        with open(args.device_config) as deviceConfigFile:
            try:
                device_config = json.load(deviceConfigFile)
            except json.JSONDecodeError:
                logging.error("Couldn't load configData")
                exit(1)
            config.__dict__["deviceConfig"] = device_config
    except FileNotFoundError:
        logging.error("Invalid path to device configuration JSON file. Exitting.")
        exit(1)

    poll()


if __name__ == '__main__':
    main()
