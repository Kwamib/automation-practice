#!/bin/bash
# Set up Lesson 2's server: the bookshop's web page on nginx, and patch-server
# as a weekly service that reports each run to Healthchecks.io.
# Safe to run again (vagrant provision). It installs nginx, but no updates:
# those are what the lesson is about.
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "setup.sh: run me as root" >&2; exit 1; }
step() { echo "==> $*"; }
apt_opts=(-o DPkg::Lock::Timeout=600)
export DEBIAN_FRONTEND=noninteractive

step "the bookshop's web page, served by nginx"
if ! command -v nginx >/dev/null; then
	apt-get "${apt_opts[@]}" -qq update
	apt-get "${apt_opts[@]}" -qq -y install nginx >/dev/null
fi
echo "<h1>The bookshop</h1><p>bookshop is up</p>" >/var/www/html/index.html
systemctl enable --now nginx >/dev/null 2>&1
curl -fsS http://127.0.0.1/ | grep -q "bookshop is up" && echo "    answering on port 80"

step "the scripts"
install -m 755 /practice/server/patch-server /usr/local/bin/patch-server
install -m 755 /practice/server/hc-ping /usr/local/bin/hc-ping

step "the Healthchecks.io ping URL, readable by root only"
install -d -m 755 /etc/patch-server
if [ -s /practice/.healthchecks-url ] && grep -Eq '^https://hc-ping\.com/[A-Za-z0-9_/-]+[[:space:]]*$' /practice/.healthchecks-url; then
	install -m 600 -o root -g root /practice/.healthchecks-url /etc/patch-server/ping-url
	echo "    installed (not shown: it's a secret)"
elif [ -s /practice/.healthchecks-url ]; then
	rm -f /etc/patch-server/ping-url
	echo "    .healthchecks-url doesn't hold a ping URL (it should start https://hc-ping.com/): runs won't be reported"
else
	echo "    no .healthchecks-url in the practice folder: runs won't be reported"
fi

step "the service and the timer"
install -m 644 /practice/server/patch-server.service /etc/systemd/system/
install -m 644 /practice/server/patch-server.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now patch-server.timer
systemctl list-timers patch-server.timer --no-pager
