#!/bin/bash

pip freeze | xargs pip uninstall -y
pip install -r requirements/production.txt

mkdir -p libs
find venv/lib/python2.7/site-packages/ -maxdepth 1 -mindepth 1 \
    -not -name "*.egg*" -type d -exec cp -r {} libs \;
cp venv/lib/python2.7/site-packages/six.py libs

$GAE_DIR/google_appengine/appcfg.py --oauth2_refresh_token=$REFRESH_TOKEN update .
rm -rf libs
