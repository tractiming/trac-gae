trac-gae
====

google appengine code for the trac platform

[![Build Status](https://img.shields.io/shippable/55e26f9a1895ca447410d895.svg)](https://app.shippable.com/projects/55e26f9a1895ca447410d895)

### Getting started
Follow these steps to get the development server up and running on your local
machine.

1. Clone the source code
   ```
   $ mkdir trac-dev && cd trac-dev
   $ git clone https://github.com/elliothevel/trac-gae.git
   $ cd trac-gae
   ```

2. Set up a virtual environment and install the dependencies
   ```
   $ virtualenv venv
   $ source venv/bin/activate
   $ pip install --no-deps \
       -r requirements/production.txt \
       -r requirements/test.txt
   ```

3. Sync the database (by default into a SQLite database, see
   `settings.common.py` for more info)
   ```
   $ ./manage.py syncdb
   ```
   Enter your superuser information when prompted.

4. Install some test data from the test fixtures
   ```
   $ ./manage.py loaddata fixture.json trac_min.json teams.json
   ```
   This also creates an account with username `alsal` that has some sample
   results.

5. Start the development server
   ```
   $ ./manage.py runserver
   ```
   Go to `http://localhost:8000/` to see the site.

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
