#!/usr/bin/env python3

import subprocess
import shutil
import os
import csv
import sys


CSV_NAME = "failed-hashes.csv"


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


def write_csv(entries, name=CSV_NAME):
    with open(name, "w") as file:
        handler = csv.writer(file)
        handler.writerow(["Path", "Package", "Changed"])
        for entry in entries:
            handler.writerow(entry)


def distro_sig_check():
    if shutil.which("apt"):
        return apt_check_integrity()
    elif shutil.which("dnf"):
        return dnf_check_integrity()
    return None


if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Need root perms...")
        sys.exit(2)

    csv_name = CSV_NAME if len(sys.argv) != 2 else sys.argv[1]
    print("Comparing ALL installed packages!\nThis should take a minute...")
    entries = distro_sig_check()
    if not entries:
        print("Failed to get entries")
        sys.exit(1)
    print("Outputted the csv: ", csv_name)
    write_csv(entries, csv_name)
