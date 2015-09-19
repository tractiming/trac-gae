#!/bin/bash

pip freeze | xargs pip uninstall -y
pip install -r requirements/production.txt

mkdir -p libs
find venv/lib/python2.7/site-packages/ -maxdepth 1 -mindepth 1 \
    -not -name "*.egg*" -type d -exec cp -r {} libs \;

appcfg.py update .
rm -rf libs
