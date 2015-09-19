#!/bin/bash

pip freeze | xargs pip uninstall -y
pip install -r requirements/production.txt

mkdir -p libs
SITE_DIR=`python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())"`
find $SITE_DIR/ -maxdepth 1 -mindepth 1 \
    -not -name "*.egg*" -type d -exec cp -r {} libs \;
cp $SITE_DIR/six.py libs

$GAE_DIR/google_appengine/appcfg.py --oauth2_refresh_token=$REFRESH_TOKEN update .
rm -rf libs
