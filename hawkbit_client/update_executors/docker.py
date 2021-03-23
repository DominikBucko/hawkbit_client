import os
import sh
import pwd
import subprocess
import logging
from ..exceptions import *


def demote(user_uid, user_gid, user_name):
    os.initgroups(user_name, user_gid)
    os.setuid(user_uid)


class Executor:
    def __init__(self, update_agent, deployment, dir):
        self.update_agent = update_agent
        self.deployment = deployment
        self.env = os.environ.copy()
        self.dir = dir

    def sudo_execute(self, command):
        process = subprocess.Popen(
            command, cwd=self.deployment['package']['dir'], shell=True
        )
        result = process.wait()
        if result != 0:
            raise UpdateExecutorException(f"Command {command} failed with status: {result}")

    def execute_command(self, command):
        if self.deployment["user"] != "default":
            pw_record = pwd.getpwnam(self.deployment["user"])
            user_name = pw_record.pw_name
            user_home_dir = pw_record.pw_dir
            user_uid = pw_record.pw_uid
            user_gid = pw_record.pw_gid
            env = os.environ.copy()
            env['HOME'] = user_home_dir
            env['LOGNAME'] = user_name
            env['PWD'] = self.deployment['package']['dir']
            env['USER'] = user_name
            process = subprocess.Popen(
                command, preexec_fn=demote(user_uid, user_gid, self.deployment["user"]),
                cwd=self.deployment['package']['dir'], env=env, shell=True
            )
            result = process.wait()
            if result != 0:
                raise UpdateExecutorException(f"Command {command} failed with status: {result}")

    def before(self):
        script = self.deployment["package"]["before_script"]
        self.execute_command(["bash", script])

    def after(self):
        script = self.deployment["package"]["after_script"]
        self.execute_command(["bash", script])

    def stop_service(self):
        cmd = f"systemctl stop {self.deployment['instance_name']}.service"
        self.sudo_execute(cmd)

    def docker_run_cmd(self):
        cmd = f"docker run -d {' '.join(self.deployment['package']['image']['run_flags'])} " \
              f"{self.deployment['package']['image']['name']}"
        self.sudo_execute(cmd)

    def docker_stop_containers_of_image(self):
        cmd = f"docker stop $(docker ps -q --filter ancestor={self.deployment['package']['image']['name']} )"
        self.sudo_execute(cmd)

    def docker_remove_containers_of_image(self):
        cmd = f"docker rm $(docker ps -q --filter ancestor={self.deployment['package']['image']['name']} )"
        self.sudo_execute(cmd)

    def start_service(self):
        cmd = f"systemctl start {self.deployment['instance_name']}.service"
        self.sudo_execute(cmd)

    def restart_service(self):
        cmd = f"systemctl restart {self.deployment['instance_name']}.service"
        self.sudo_execute(cmd)

    def persist_old_image(self):
        cmd = f"docker image save -o '{self.deployment['package']['image']['name']}-old'"
        self.sudo_execute(cmd)

    def reload_old_image(self):
        cmd = f"docker image load < {self.deployment['package']['image']['name']}-old"
        self.sudo_execute(cmd)

    def delete_image(self):
        cmd = f"docker image rm {self.deployment['package']['image']['name']}"
        self.sudo_execute(cmd)

    def load_image(self):
        cmd = f"docker image load < {self.deployment['package']['image']['file']}"
        self.sudo_execute(cmd)

    def execute(self):
        sh.cp(f"{self.dir}/{self.deployment['package']['image']['file']}", f"{self.deployment['package']['dir']}/")
        if self.deployment['package'].get('before_script'):
            self.before()
        try:
            if self.deployment["daemon"] == "systemd":
                self.stop_service()
            elif self.deployment["daemon"] == "docker":
                self.docker_stop_containers_of_image()
        except UpdateExecutorException:
            logging.error("No instances running currently.")

        if self.deployment['package']['image'].get("persist_old"):
            try:
                self.persist_old_image()
            except UpdateExecutorException as e:
                if self.deployment["daemon"] == "systemd":
                    self.restart_service()
                elif self.deployment["daemon"] == "docker":
                    self.docker_run_cmd()
                logging.error("Couldnt persist old image.")
                raise e

        try:
            self.delete_image()
        except UpdateExecutorException as e:
            # self.reload_old_image()
            # if self.deployment["daemon"] == "systemd":
            #     self.restart_service()
            # elif self.deployment["daemon"] == "docker":
            #     self.docker_run_cmd()
            logging.error("Couldn't delete old image")
            # raise e

        self.load_image()

        if self.deployment["daemon"] == "systemd":
            self.restart_service()
        elif self.deployment["daemon"] == "docker":
            self.docker_run_cmd()

        if self.deployment['package'].get('after_script'):
            self.after()

        self.update_agent.send_feedback(execution="closed",
                                        finished="success",
                                        progress={"cnt": 1, "of": 1},
                                        details=["Finished updating."]
                                        )

        logging.info("Updating completed successfully.")
