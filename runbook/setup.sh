#!/bin/bash
# Set up Lesson 5's server: a small disk for the bookshop's logs, the app
# writing to it, the runbook, and the fix-disk-full script.
# Running it again (vagrant provision) starts the lab over, with an empty disk.
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "setup.sh: run me as root" >&2; exit 1; }
step() { echo "==> $*"; }

step "a user for the app"
id bookshop >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin bookshop

step "a small (200 MB) disk for the logs, at /srv/bookshop-logs"
systemctl stop bookshop 2>/dev/null || true
if mountpoint -q /srv/bookshop-logs; then umount /srv/bookshop-logs; fi
rm -f /var/lib/bookshop-logs.img
fallocate -l 200M /var/lib/bookshop-logs.img
mkfs.ext4 -q -F -m 0 -L bookshop-logs /var/lib/bookshop-logs.img
install -d /srv/bookshop-logs
mount -o loop /var/lib/bookshop-logs.img /srv/bookshop-logs
chown bookshop:bookshop /srv/bookshop-logs
chmod 755 /srv/bookshop-logs

step "the app, writing a log line every second"
install -m 755 /practice/runbook/bookshop-app /usr/local/bin/bookshop-app
install -m 644 /practice/runbook/bookshop.service /etc/systemd/system/bookshop.service
systemctl daemon-reload
systemctl enable --now bookshop 2>/dev/null

step "the runbook, and the script it becomes"
install -m 644 -o vagrant -g vagrant /practice/runbook/RUNBOOK.md /home/vagrant/RUNBOOK.md
install -m 755 /practice/runbook/fix-disk-full /usr/local/sbin/fix-disk-full
rm -rf /var/lib/incidents /var/log/runbook.log

sleep 2
df -h /srv/bookshop-logs
