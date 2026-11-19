#!/bin/bash
# Set up Lesson 6's server: PostgreSQL with the bookshop's database, two logins
# for the app (bookshop_a in use, bookshop_b the standby), the app itself, and
# the rotation script.
# Running it again (vagrant provision) starts the lab over, with new passwords.
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "setup.sh: run me as root" >&2; exit 1; }
step() { echo "==> $*"; }
export DEBIAN_FRONTEND=noninteractive
apt_opts=(-o DPkg::Lock::Timeout=600)

step "PostgreSQL, and Python's PostgreSQL library"
if ! command -v psql >/dev/null || ! python3 -c 'import psycopg2' 2>/dev/null; then
	apt-get "${apt_opts[@]}" -qq update
	apt-get "${apt_opts[@]}" -qq -y install postgresql python3-psycopg2 >/dev/null
fi
systemctl enable --now postgresql >/dev/null 2>&1

step "a user for the app"
id bookshop >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin bookshop

step "the bookshop database, starting over"
systemctl stop bookshop-app 2>/dev/null || true
pw=$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')
runuser -u postgres -- psql -X -q -v ON_ERROR_STOP=1 <<SQL
DROP DATABASE IF EXISTS bookshop;
DROP ROLE IF EXISTS bookshop_a;
DROP ROLE IF EXISTS bookshop_b;
DROP ROLE IF EXISTS bookshop;
CREATE ROLE bookshop NOLOGIN;
CREATE ROLE bookshop_a LOGIN PASSWORD '$pw' IN ROLE bookshop;
CREATE ROLE bookshop_b NOLOGIN IN ROLE bookshop;
CREATE DATABASE bookshop;
SQL
runuser -u postgres -- psql -X -q -v ON_ERROR_STOP=1 -d bookshop <<'SQL'
CREATE TABLE books (isbn text PRIMARY KEY, title text NOT NULL);
INSERT INTO books VALUES
  ('9780141439518', 'Pride and Prejudice'),
  ('9780451524935', 'Nineteen Eighty-Four'),
  ('9780316769488', 'The Catcher in the Rye'),
  ('9780061120084', 'To Kill a Mockingbird'),
  ('9780743273565', 'The Great Gatsby');
GRANT SELECT ON books TO bookshop;
SQL

step "the app's database login, readable by root and the app only"
install -d -m 755 /etc/bookshop
printf 'DB_USER=bookshop_a\nDB_PASSWORD=%s\n' "$pw" >/etc/bookshop/db.env
chown root:bookshop /etc/bookshop/db.env
chmod 640 /etc/bookshop/db.env
rm -f /etc/bookshop/db.env.previous /var/log/db-rotation.log

step "the app, the rotation script and the watcher"
install -m 755 /practice/rotate/bookshop-app /usr/local/bin/bookshop-app
install -m 755 /practice/rotate/watch-app /usr/local/bin/watch-app
install -m 755 /practice/rotate/rotate-db-password /usr/local/sbin/rotate-db-password
install -m 644 /practice/rotate/bookshop-app.service /etc/systemd/system/bookshop-app.service
systemctl daemon-reload
systemctl enable --now bookshop-app >/dev/null 2>&1
systemctl restart bookshop-app
sleep 2
curl -s http://127.0.0.1:8080/books
