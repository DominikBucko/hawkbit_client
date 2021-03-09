import os
import sh
import pwd
import subprocess
from exceptions import *


def demote(user_uid, user_gid, user_name):
    os.initgroups(user_name, user_gid)
    os.setuid(user_uid)


class Executor:
    def __init__(self, deployment, dir):
        self.deployment = deployment
        self.env = os.environ.copy()
        self.dir = dir

    def sudo_execute(self, command):
        process = subprocess.Popen(
            command, cwd=self.deployment['target']['dir'], shell=True
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
            env['PWD'] = self.deployment['target']['dir']
            env['USER'] = user_name
            process = subprocess.Popen(
                command, preexec_fn=demote(user_uid, user_gid, self.deployment["user"]),
                cwd=self.deployment['target']['dir'], env=env, shell=True
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
        cmd = f"systemctl stop {self.deployment['target']['service']}.service"
        self.sudo_execute(cmd)

    def start_service(self):
        cmd = f"systemctl start {self.deployment['target']['service']}.service"
        self.sudo_execute(cmd)

    def persist_old_image(self):
        cmd = f"docker image save -o '{self.deployment['package']['image']['name']}-old'"
        self.sudo_execute(cmd)

    def delete_image(self):
        cmd = f"docker image delete {self.deployment['package']['image']['name']}"
        self.sudo_execute(cmd)

    def load_image(self):
        cmd = f"docker image load < {self.deployment['package']['image']['name']}"
        self.sudo_execute(cmd)

    def execute(self):
        sh.cp(f"{self.dir}/{self.deployment['package']['image']['file']}", f"{self.deployment['target']['dir']}/")
        if self.deployment['package'].get('before_script'):
            self.before()

        self.stop_service()
        self.persist_old_image()
        self.delete_image()
        self.load_image()
        self.start_service()

