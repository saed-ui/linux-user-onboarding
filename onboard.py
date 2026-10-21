# onboards new hires from a csv: creates the user, puts them in their dept group,
# sets a temp password they have to change on first login, locks down their home dir
#
# usage: sudo python3 onboard.py new_hires.csv
#        python3 onboard.py new_hires.csv --dry-run   (just prints what it'd do)

import csv
import os
import re
import secrets
import string
import subprocess
import sys

dept_groups = {
    "HR": "hr_group",
    "IT": "it_group",
    "Finance": "finance_group",
    "Sales": "sales_group",
}

dry = "--dry-run" in sys.argv
args = [a for a in sys.argv[1:] if a != "--dry-run"]
hires_file = args[0] if args else "new_hires.csv"


def run(cmd, stdin=None):
    if dry:
        print("  [dry]", " ".join(cmd))
        return True
    r = subprocess.run(cmd, input=stdin, text=True, capture_output=True)
    if r.returncode != 0:
        print("  error:", r.stderr.strip())
    return r.returncode == 0


def exists(cmd):
    # getent returns 0 if the user/group is there
    return subprocess.run(cmd, capture_output=True).returncode == 0


def make_password(n=14):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        pw = "".join(secrets.choice(chars) for _ in range(n))
        # make sure it actually has a mix
        if (any(c.islower() for c in pw) and any(c.isupper() for c in pw)
                and any(c.isdigit() for c in pw) and any(c in "!@#$%^&*" for c in pw)):
            return pw


if not dry and os.geteuid() != 0:
    sys.exit("needs root. run with sudo (or use --dry-run)")

created = []

with open(hires_file) as f:
    for row in csv.DictReader(f):
        name = row["Name"].strip()
        dept = row["Department"].strip()
        user = row["Target_Username"].strip().lower()
        print(f"\n{name} ({dept}) -> {user}")

        # linux usernames: lowercase, start with a letter, max 32 chars
        if not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", user):
            print("  skipping, bad username")
            continue
        if exists(["getent", "passwd", user]):
            print("  skipping, user already exists")
            continue

        group = dept_groups.get(dept)
        if not group:
            print(f"  skipping, no group set up for dept '{dept}'")
            continue
        if not exists(["getent", "group", group]):
            run(["groupadd", group])

        # -m makes the home dir, -c puts their real name in the comment field
        if not run(["useradd", "-m", "-s", "/bin/bash", "-c", name, "-G", group, user]):
            continue

        pw = make_password()
        run(["chpasswd"], stdin=f"{user}:{pw}\n")
        run(["chage", "-d", "0", user])           # forces password change on first login
        run(["chmod", "700", f"/home/{user}"])    # only the user can touch their stuff

        created.append((name, user, group, pw))
        print("  done")

# temp passwords go in a file only root can read, not the screen
if created and not dry:
    out = "onboarded_creds.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "username", "group", "temp_password"])
        w.writerows(created)
    os.chmod(out, 0o600)
    print(f"\n{len(created)} user(s) created. temp passwords in {out} (chmod 600, delete after handing them out)")
elif dry:
    print(f"\ndry run, {len(created)} user(s) would be created")
