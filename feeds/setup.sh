#!/bin/bash
# Set up Lesson 3's server: a folder the supplier drops stock files into, and
# feed-loader, started by systemd whenever a file arrives.
# Running it again (vagrant provision) starts the lab over: it empties the
# folders and puts the stock list back as it was.
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "setup.sh: run me as root" >&2; exit 1; }
step() { echo "==> $*"; }

step "a user for the job, feeds, with no password and no login"
id feeds >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin feeds
usermod -aG feeds vagrant   # so you can drop files in, as the supplier would

step "the feed folders: incoming, processed and failed"
systemctl stop feed-loader.path 2>/dev/null || true
rm -rf /srv/feeds
install -d -o feeds -g feeds -m 755 /srv/feeds
install -d -o feeds -g feeds -m 2775 /srv/feeds/incoming /srv/feeds/processed /srv/feeds/failed

step "the bookshop's stock list, as it was before any files arrived"
install -d -o feeds -g feeds -m 755 /srv/bookshop
printf '%s\n' "isbn,title,quantity" \
	"9780141439518,Pride and Prejudice,3" \
	"9780451524935,Nineteen Eighty-Four,0" \
	"9780316769488,The Catcher in the Rye,5" >/srv/bookshop/stock.csv
chown feeds:feeds /srv/bookshop/stock.csv
chmod 644 /srv/bookshop/stock.csv

step "the loader"
install -m 755 /practice/feeds/feed-loader /usr/local/bin/feed-loader

step "the path unit and the service"
install -m 644 /practice/feeds/feed-loader.service /practice/feeds/feed-loader.path /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now feed-loader.path
systemctl status feed-loader.path --no-pager | head -3
