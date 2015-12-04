#!/bin/bash

mkdir -p libs
pip freeze | xargs pip uninstall -y
pip install -r requirements/production.txt -t libs
$GAE_DIR/google_appengine/appcfg.py --oauth2_refresh_token=$REFRESH_TOKEN update .
rm -rf libs
