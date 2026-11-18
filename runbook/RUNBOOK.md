# Runbook: the bookshop logs disk is full

**Alert:** "/srv/bookshop-logs is over 80% full" on the bookshop server.
**Impact:** when it reaches 100%, the app can't write its log, and errors go unrecorded.

1. Log in to the server, and check how full the disk is:

       df -h /srv/bookshop-logs

2. Find what's using the space:

       sudo du -ah /srv/bookshop-logs | sort -rh | head

3. If `app.log` is huge, someone has probably left debug logging on. Switch it off:

       sudo systemctl kill --kill-whom=main -s USR2 bookshop

4. Delete the big log:

       sudo rm /srv/bookshop-logs/app.log

5. Check the disk again with `df -h /srv/bookshop-logs`. It should be nearly empty.

6. Post in the incident channel that it's fixed.
