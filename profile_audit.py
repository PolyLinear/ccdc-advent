#!/usr/bin/env python3

import subprocess
import os
import json
import sys

import utils


class User:
    def __init__(self, passwd_entry: str):
        self._name: str = passwd_entry[:passwd_entry.find(':')]
        self._shell: str = passwd_entry[passwd_entry.rfind(':')+1:].rstrip()

        sudo_proc = subprocess.run(
            ['sudo', '-l', '-U', self.name], capture_output=True)
        self._privilege: bool = b"not allowed" not in sudo_proc.stdout
        if self._privilege:
            utils.err_print(sudo_proc.stdout.decode())

        # checking common login shells
        self._interactive: bool = False
        for shell in ["/bash", "/sh", "/zsh", "/ksh", "/csh", "/dash"]:
            if self.shell.rfind(shell) != -1:
                self._interactive = True
                break

    @property
    def name(self):
        """str rep of username """
        return self._name

    @property
    def shell(self):
        """str rep of login shell"""
        return self._shell

    @property
    def interactive(self):
        """bool rep of interactive state; True if interactive, False otherwise"""
        return self._interactive

    @property
    def privilege(self):
        """bool rep of privilege state; True if they are, False otherwise"""
        return self._privilege

    def json_dict(self):
        return {"name": self.name, "shell": self.shell, "privilege": self.privilege, "interactive": self.interactive}


def get_users(): 
    result = []
    with open("/etc/passwd", "r") as file:
        for line in file.readlines():
            result.append(User(line))
    return result


def output_json(users , file):

    format = {
        "users": [],
        "privilege": [],
        "interactive": [],
    }

    for user in users:
        user_dict = user.json_dict()
        format["users"].append(user_dict)
        if user.privilege:
            format["privilege"].append(user_dict)
        if user.interactive:
            format["interactive"].append(user_dict)

    json.dump(format, file, indent=2)


def run(stdout=True) -> bool:

    # need effective UID to be 0 (priv)
    if os.geteuid() != 0:
        utils.err_print("Please run with root priv", file=sys.stderr)
        return False

    users = get_users()

    if not stdout:
        with open(os.uname().nodename+"-profile-audit.json", "w") as f:
            output_json(users, f)
    else:
        output_json(users, sys.stdout)
    return True


if __name__ == "__main__":
    if not run(stdout=False):
        sys.exit(1)
