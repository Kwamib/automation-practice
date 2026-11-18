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

Lesson 2 runs on a small virtual machine, made by
[Vagrant](https://developer.hashicorp.com/vagrant) from the `Vagrantfile` here,
as in the Linux track from its Lesson 7. This folder appears inside it at `/practice`:

    vagrant up          # builds it: runs server/setup.sh
    vagrant ssh
    vagrant destroy -f  # when you're done

- `server/setup.sh` installs `error-report` as a service, run every 5 minutes by
  a timer, as its own user, and is safe to run again (`vagrant provision`).
- `server/hc-ping` tells Healthchecks.io how each run ended.
- `.healthchecks-url` is where your check's ping URL goes. It's a secret: it's
  in `.gitignore`, and nothing here prints it.
