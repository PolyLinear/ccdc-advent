#!/usr/bin/env python3

import subprocess
import shutil
import os
import sys

import utils
import json




def install_debsums():
    program = ["apt-get", "install", "-y",  "debsums"]
    env = {"DEBIAN_FRONTEND": "noninteractive"}
    return subprocess.run(program, env=env, capture_output=True).returncode == 0


def apt_check_integrity():
    program = ["debsums", "-s", "-a"]
    if not shutil.which(program[0]) and not install_debsums():
        return None

    debsums_proc = subprocess.run(program, capture_output=True)
    result = []
    for lines in debsums_proc.stderr.splitlines():

        # could use regex here, but the output is predictable
        # enough where we can split on whitespace
        tokens = lines.split()
        path = tokens[3].decode()
        package = tokens[5].decode()

        # padding the rightmost entry with periods for parity with rpms verify output
        result.append([path, package,  '.' * 9])
    return result


def dnf_check_integrity():

    # RHEL system; query files that were installed from rpm packages
    program = ["rpm", "-Va"]
    rpm_proc = subprocess.run(program, capture_output=True)

    # process each row in the output
    result = []
    for line in rpm_proc.stdout.splitlines():

        # dirty solution, could use regex capture groups instead
        line = line.split()
        changed = line[0].decode()
        path = line[2].decode()

        # output of 'rpm -Va' doesn't specify the origin packages
        # need to query
        package_proc = subprocess.run(
            ["rpm", "-qf", path, "--qf", '%{NAME}'], capture_output=True)
        package = package_proc.stdout.decode().strip()

        result.append([path, package, changed])
    return result


def output_json(entries, file):
    format = {
        "packages": [] 
    }

    for path, package, changed in entries:
        format["packages"].append({"path": path, "package": package, "changed": changed})
    json.dump(format, file)

    
def distro_sig_check():
    if shutil.which("apt"):
        return apt_check_integrity()
    elif shutil.which("dnf"):
        return dnf_check_integrity()
    return None



def run(stdout=True) -> bool:
    if os.getuid() != 0:
        utils.err_print("Need root perms...")
        return False


    users = distro_sig_check()
    if not users:
        return False

    if not stdout:
        with open(os.uname().nodename+"-sig-check.json", "w") as f:
            output_json(users, f)
    else:
        output_json(users, sys.stdout)


    return True



if __name__ == "__main__":
    if not run(stdout=False):
        sys.exit(1)
    
