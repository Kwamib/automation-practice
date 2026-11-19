# automation-practice

Practice files for the Automation track on [kwamib.dev](https://kwamib.dev/resources/automation).
Everything here is made up: the bookshop, its logs and its backups. It picks up where
the Linux and Python tracks leave off.

Lesson 1 runs in a container with this folder inside it, like the Linux track's
first lessons:

    docker run -it --rm -v "$PWD":/practice -w /practice ubuntu:24.04 bash

- `make-fake-backups /lab` builds a folder of 30 nights of fake backups, dated
  with `touch` so each looks as old as its name says, plus some traps: a copy
  with a space in its name, a half-written `.part` file, links, a `monthly/`
  folder, and a second server whose backups stopped. Run it again to start over.
  Use a folder inside the container, like `/lab`: the lesson deletes things there.
- `prune-backups` deletes old backups safely: a dry run unless you add
  `--apply`, guard rails against the wrong folder, and it always keeps the
  newest 7.

Lesson 2 runs on a small Ubuntu web server, `web-1`, made by
[Vagrant](https://developer.hashicorp.com/vagrant) from the `Vagrantfile` here,
as in the Linux track from its Lesson 7. This folder appears inside it at `/practice`:

    vagrant up                              # builds it: runs server/setup.sh
    vagrant snapshot save before-patch      # a restore point
    vagrant ssh
    vagrant snapshot restore before-patch   # undo the patching
    vagrant destroy -f                      # when you're done

- `server/setup.sh` installs nginx with the bookshop's page, and `patch-server`
  as a weekly service on a timer. It installs no updates: those are the lesson.
- `server/patch-server` lists pending updates (a dry run), or with `--apply`
  installs them, restarts the app and checks it still works.
- `server/hc-ping` tells Healthchecks.io how each run ended.
- `.healthchecks-url` is where your check's ping URL goes. It's a secret: it's
  in `.gitignore`, and nothing here prints it.

Lesson 3 runs on its own server, `feeds`, from the `Vagrantfile` in `feeds/`:

    cd feeds
    vagrant up          # builds it: runs feeds/setup.sh
    vagrant ssh
    vagrant provision   # starts the lab over
    vagrant destroy -f  # when you're done

- `feeds/feed-loader` checks each supplier stock file that arrives in
  `/srv/feeds/incoming`, loads good ones into the stock list and moves them to
  `processed/`, and moves bad ones to `failed/` with a `.reason` file.
- `feeds/feed-loader.path` starts it whenever a `.csv` file arrives.
- `feeds/samples/` holds a good file, an update, and two bad ones.

Lesson 4 runs on its own server, `office`, from the `Vagrantfile` in `users/`:

    cd users
    vagrant up          # builds it: runs users/setup.sh
    vagrant ssh
    vagrant provision   # starts the lab over
    vagrant destroy -f  # when you're done

- `users/staff` adds people (`add`), removes every kind of access they had
  (`remove`), shows who can get in (`audit`), and makes the server match a
  roster (`sync`). Changes are dry runs unless you add `--apply`.
- `users/roster.csv` lists who should have access.

Lesson 5 runs on its own server, `bookshop-1`, from the `Vagrantfile` in `runbook/`:

    cd runbook
    vagrant up          # builds it: runs runbook/setup.sh
    vagrant ssh
    vagrant provision   # starts the lab over, with an empty disk
    vagrant destroy -f  # when you're done

- `runbook/RUNBOOK.md` is the runbook for a full log disk, as it was written
  (one of its steps is wrong: the lesson finds out which).
- `runbook/fix-disk-full` is the runbook as a script: it looks first, asks you
  to type the server's name, fixes it, checks the fix, and keeps a record.
- `runbook/bookshop-app` stands in for the app; USR1 switches on debug logging.

Lesson 6 runs on its own server, `db-1`, from the `Vagrantfile` in `rotate/`:

    cd rotate
    vagrant up          # builds it: runs rotate/setup.sh (installs PostgreSQL)
    vagrant ssh
    vagrant provision   # starts the lab over, with new passwords
    vagrant destroy -f  # when you're done

- `rotate/rotate-db-password` rotates the app's database password with no
  downtime: it gives the standby login a new password, tests it, reloads the
  app onto it, checks, and only then switches the old login off.
- `rotate/bookshop-app` stands in for the app; a reload makes it log in again
  without stopping.
- `rotate/watch-app SECONDS` counts failed requests while you work.

Lesson 7 runs in Docker, with no server: a Python container, and Mailpit, a
fake mail server that catches the email so nothing real is sent.

    cd report
    docker network create report-lab
    docker run -d --name mailpit --network report-lab -p 8025:8025 axllent/mailpit
    docker run -it --rm --network report-lab -v "$PWD":/practice -w /practice python:3.12-slim bash

- `report/make_sales.py` makes a week of branch sales spreadsheets with the
  problems real ones have; `--resend` makes the corrected ones.
- `report/naive.py` adds them up the quick way (and gets it wrong).
- `report/weekly_report.py` checks every file, builds an Excel report, and
  emails it with `--send`. Its tests are in `report/test_weekly_report.py`.
