import os
import sh
import pwd
import subprocess
import sys


def demote(user_uid, user_gid, user_name):
    def result():
        os.initgroups(user_name, user_gid)
        os.setuid(user_uid)

    return result


class Executor:
    def __init__(self, deployment, dir):
        self.deployment = deployment
        self.env = os.environ.copy()
        self.dir = dir

    def execute(self):
        if self.deployment["platform"] == "docker":
            sh.cp(f"{self.dir}/{self.deployment['package']['image']}", f"{self.deployment['target']['dir']}/")
            command = f"docker load < {self.deployment['package']['image']}"
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
                    cwd=self.deployment['target']['dir'], env=env
                )
                result = process.wait()
                print(result)
