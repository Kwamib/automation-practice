# automation-practice

Practice files for the Automation track on [kwamib.dev](https://kwamib.dev/resources/automation).
Everything here is made up: the bookshop, its logs and its errors. It picks up where
the Linux and Python tracks leave off.

Lesson 1 runs in a container with this folder inside it, like the Linux track's
first lessons:

    docker run -it --rm -v "$PWD":/practice -w /practice ubuntu:24.04 bash

- `logs/` holds two days of the bookshop's app logs from two web servers, in
  `web-1/`, `web-2/` and `old logs/` (the space in that name is on purpose).
- `error-report` counts each distinct error in those logs, most frequent first,
  and is safe to run unattended. `./error-report --dry-run` changes nothing.
- `reports/` is where the reports go. It isn't kept in Git.

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
