#!/usr/bin/env python3

import subprocess
import os 
import json
from typing import List


class User:
    def __init__(self, passwd_entry: str) -> None:
        self._name: str = passwd_entry[:passwd_entry.find(':')]
        self._shell: str = passwd_entry[passwd_entry.rfind(':')+1:].rstrip()

        sudo_proc = subprocess.run(['sudo', '-l', '-U', self.name], capture_output=True)
        self._privilege: bool = b"not allowed" not in sudo_proc.stdout 
        if self._privilege:
            print(sudo_proc.stdout.decode())

        #checking common login shells
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


def get_users() -> List[User]: 
    result = []
    with open("/etc/passwd", "r") as file:
        for line in file.readlines():
            result.append(User(line))
    return result 



def output_json(users: List[User]) -> None:

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

    with open("user-audit.json", "w") as f:
        json.dump(format, f, indent=2)


def run() -> None:

    #need effective UID to be 0 (priv)
    if os.geteuid() != 0:
        print("Please run with root priv")
        return 

    users = get_users()
    output_json(users)

    
if __name__ == "__main__":
    run()
