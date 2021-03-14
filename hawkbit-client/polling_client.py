from .config import config
from .exceptions import *
from .misc import parse_time_to_seconds
from .update_agent import UpdateAgent, get_deployment_base_ref
import time
import logging
import requests
import json


def push_config(link):
    resp = requests.put(url=link,
                        headers={
                            "Accept": "application/hal+json",
                            "Authorization": f"TargetToken {config.TargetToken}",
                            "Content-Type": f"application/json"
                        },
                        data=json.dumps(config.deviceConfig))

    if resp.status_code in range(200, 299):
        return
    else:
        raise ConfigPushError(f"Status code: {resp.status_code}, msg: {resp.content}")


def poll():
    sleep = 5 * 60
    resp = requests.get(url=f"http://{config.updateServerUrl}/DEFAULT/controller/v1/{config.controllerId}",
                        headers={
                            "Accept": "application/hal+json",
                            "Authorization": f"TargetToken {config.TargetToken}"
                        })

    if resp.status_code in range(200, 299):
        data = resp.json()
    else:
        logging.error(
            f"Error while polling update server. "
            f"Status code {resp.status_code} on request {resp.request}. "
            f"Response: {resp.content}")
        time.sleep(sleep)


    if data.get("_links"):
        if data["_links"].get("configData"):
            push_config(data["_links"]["configData"]["href"])
        elif data["_links"].get("deploymentBase"):
            agent = UpdateAgent(get_deployment_base_ref(data["_links"]["deploymentBase"]["href"]))
            agent.download_files()


    else:
        try:
            sleep = parse_time_to_seconds(data["config"]["polling"]["sleep"])

        except KeyError:
            logging.error(f"Invalid sleep data - resp content: {data}, defaulting to last value ({sleep}).")

    time.sleep(sleep)
