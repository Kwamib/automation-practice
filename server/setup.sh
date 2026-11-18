#!/bin/bash
# Set up Lesson 2's server: the error report as a service, run every 5 minutes
# by a timer, as its own user, reporting each run to Healthchecks.io.
# Safe to run again (vagrant provision): it puts each file in place and
# changes nothing that's already right.
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "setup.sh: run me as root" >&2; exit 1; }
step() { echo "==> $*"; }

step "a user for the job, with no password and no login"
id reporter >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin reporter

step "the bookshop's logs, readable by everyone, as a web server leaves them"
install -d -m 755 /srv/bookshop
rm -rf /srv/bookshop/logs
cp -r /practice/logs /srv/bookshop/logs
chown -R root:root /srv/bookshop/logs
find /srv/bookshop/logs -type d -exec chmod 755 {} +
find /srv/bookshop/logs -type f -exec chmod 644 {} +

step "a folder for the reports, owned by the job's user"
install -d -o reporter -g reporter -m 755 /srv/reports

step "the scripts"
install -m 755 /practice/error-report /usr/local/bin/error-report
install -m 755 /practice/server/hc-ping /usr/local/bin/hc-ping

step "the Healthchecks.io ping URL, readable by root and the job only"
install -d -m 755 /etc/error-report
if [ -s /practice/.healthchecks-url ] && grep -Eq '^https://hc-ping\.com/[A-Za-z0-9_/-]+[[:space:]]*$' /practice/.healthchecks-url; then
	install -m 640 -o root -g reporter /practice/.healthchecks-url /etc/error-report/ping-url
	echo "    installed (not shown: it's a secret)"
elif [ -s /practice/.healthchecks-url ]; then
	rm -f /etc/error-report/ping-url
	echo "    .healthchecks-url doesn't hold a ping URL (it should start https://hc-ping.com/): runs won't be reported"
else
	echo "    no .healthchecks-url in the practice folder: runs won't be reported"
fi

step "the service and the timer"
install -m 644 /practice/server/error-report.service /etc/systemd/system/
install -m 644 /practice/server/error-report.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now error-report.timer
systemctl list-timers error-report.timer --no-pager
