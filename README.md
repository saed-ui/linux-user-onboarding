# linux-user-onboarding

script for onboarding new hires on a linux box instead of typing useradd 50 times.

reads a csv of new people and for each one:
- creates the account + home dir
- adds them to their dept group (hr_group, it_group, etc). makes the group if it doesn't exist yet
- gives them a random temp password and forces a change on first login (`chage -d 0`)
- `chmod 700` on their home so nobody else can poke around

skips bad usernames, people who already exist, and depts with no group mapped.

## run it

```
python3 onboard.py new_hires.csv --dry-run   # see what it would do, no root needed
sudo python3 onboard.py new_hires.csv
```

csv format:

```
Name,Department,Target_Username
Sara Ahmed,HR,sahmed
```

temp passwords get written to `onboarded_creds.csv` (only root can read it). hand them out then delete the file.

**test this in a VM or container, not your main machine.** it's making real users.

## notes
- uses `subprocess.run` with list args, no `shell=True`, so a weird name in the csv can't inject commands
- passwords come from `secrets` not `random` since random isn't meant for security stuff
- to add a dept just add it to `dept_groups` at the top
