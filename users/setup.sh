#!/bin/bash
# Set up Lesson 4's server: the groups, the staff script, and SSH keys for three
# new starters, as each would make on their own computer.
# Running it again (vagrant provision) starts the lab over: it removes alice,
# bob and carol, their archives and the log.
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "setup.sh: run me as root" >&2; exit 1; }
step() { echo "==> $*"; }

step "the groups: bookshop-staff for everyone the script manages, developers and deployers for access"
groupadd -f bookshop-staff
groupadd -f developers
groupadd -f deployers

step "starting over: removing the lab's people if they're here"
for u in alice bob carol alcie carlo; do
	if id "$u" >/dev/null 2>&1; then
		pkill -KILL -u "$u" 2>/dev/null || true
		crontab -r -u "$u" 2>/dev/null || true
		userdel --remove "$u" 2>/dev/null || true
	fi
done
rm -rf /var/backups/staff /var/log/staff.log

step "a shared folder, where anyone can leave a file (like /tmp)"
install -d -m 1777 /srv/shared
rm -f /srv/shared/*

step "the staff script, for admins only"
install -m 755 /practice/users/staff /usr/local/sbin/staff

step "SSH keys for alice, bob and carol, in /home/vagrant/keys"
install -d -o vagrant -g vagrant -m 700 /home/vagrant/keys
for n in alice bob carol; do
	rm -f "/home/vagrant/keys/$n" "/home/vagrant/keys/$n.pub"
	sudo -u vagrant ssh-keygen -q -t ed25519 -N "" -C "$n@bookshop" -f "/home/vagrant/keys/$n"
done

step "the roster: who should have access"
install -o vagrant -g vagrant -m 644 /practice/users/roster.csv /home/vagrant/roster.csv
rm -f /home/vagrant/empty.csv /home/vagrant/typo.csv
ls /home/vagrant/keys
