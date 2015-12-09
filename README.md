trac-gae
====

google appengine code for the trac platform

[![Build Status](https://img.shields.io/shippable/55e26f9a1895ca447410d895.svg)](https://app.shippable.com/projects/55e26f9a1895ca447410d895)

### How to dump data for backup
```
$ python manage.py dumpdata \
    --format=json \
    --indent=4 \
    --natural \
    -e sessions \
    -e admin \
    -e contenttypes \
    -e auth.Permission \
    > mybackup.json
```
