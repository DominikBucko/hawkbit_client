import requests
import json
import logging
import shutil
import os
import yaml
import sh
from .exceptions import *
from .config import config


def get_deployment_base_ref(deploymentBaseRefUrl):
    resp = requests.get(url=deploymentBaseRefUrl,
                        headers={
                            "Accept": "application/hal+json",
                            "Authorization": f"TargetToken {config.TargetToken}"
                        })

    if resp.status_code not in range(200, 299):
        raise DeploymentBaseFetchError(f"Hawkbit status code {resp.status_code}, msg: {resp.content}")

    return resp.json(), deploymentBaseRefUrl


class UpdateAgent:
    def __init__(self, deploymentBaseRef):
        self.deploymentBaseRefUrl = deploymentBaseRef[1]
        deploymentBaseRef = deploymentBaseRef[0]
        self.id = deploymentBaseRef.get("id")
        self.deployment = deploymentBaseRef.get("deployment")
        self.updateRule = self.deployment.get("update")
        self.downloadRule = self.deployment.get("download")
        self.chunks = self.deployment.get("chunks")
        self.config = None

    def download_files(self):
        for chunk in self.chunks:
            dir = f"{config.targetDir}/{chunk['part']}/v{chunk['version']}/{chunk['name']}"
            try:
                os.makedirs(dir, exist_ok=True)
            except KeyError as e:
                raise DeploymentBaseFormatError(e)

            try:
                for artifact in chunk["artifacts"]:
                    with requests.get(url=artifact["_links"]["download-http"]["href"],
                                      headers={
                                          "Accept": "application/hal+json",
                                          "Authorization": f"TargetToken {config.TargetToken}"
                                      }, stream=True) as req:
                        with open(f"{dir}/{artifact['filename']}", mode="wb+") as file:
                            shutil.copyfileobj(req.raw, file)
            except KeyError as e:
                raise DeploymentBaseFormatError(e)

            progress = {
                "cnt": self.chunks.index(chunk) + 1,
                "of": len(self.chunks)
            }

            self.send_feedback(execution="proceeding", finished="none", progress=progress,
                               details=["Done downloading."])
            logging.info("Done downloading file.")

    def send_feedback(self, execution, finished="none", progress=None, details=None):
        if not details:
            details = []
        elif not details.__class__ == [].__class__:
            details = [details]

        body = {
            "id": f"{self.id}",
            "status": {
                "result": {
                    "progress": progress,
                    "finished": finished
                },
                "execution": execution,
                "details": details
            }
        }

        if not progress:
            body["status"]["result"].pop("progress")

        resp = requests.post(
            url=f"http://{config.updateServerUrl}/DEFAULT/controller/v1/{config.controllerId}/deploymentBase/{self.id}/feedback",
            headers={
                "Accept": "application/hal+json",
                "Content-Type": f"application/json",
                "Authorization": f"TargetToken {config.TargetToken}"
            },
            data=json.dumps(body))

        logging.info(json.dumps(body))

        if resp.status_code not in range(200, 299):
            raise FeedbackPushError

    def apply_updates(self):
        for chunk in self.chunks:
            dir = f"{config.targetDir}/{chunk['part']}/v{chunk['version']}/{chunk['name']}"
            for artifact in chunk["artifacts"]:
                sh.tar("-xvzf", f"{dir}/{artifact['filename']}")
                dirname = artifact['filename'].replace(".tar.gz", "")
                dir += f"/{dirname}"
                try:
                    self.config = yaml.safe_load(f"{dir}/example_deployment.yaml")
                except Exception:
                    return

                



