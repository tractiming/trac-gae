#!/bin/bash

pip uninstall -y django-rest-framework-stripe
pip freeze | xargs pip uninstall -y
pip install \
    --no-deps \
    -r requirements/production.txt

mkdir -p libs
SITE_DIR=`python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())"`
find $SITE_DIR/ -maxdepth 1 -mindepth 1 -type d -exec cp -r {} libs \;
cp $SITE_DIR/six.py libs

DRF_STRIPE_DIR=$(head -n 1 $SITE_DIR/django-rest-framework-stripe.egg-link)
cp -r $DRF_STRIPE_DIR/payments libs

cp -r libs/django/contrib/admin/static/admin static/
cp -r libs/rest_framework_swagger/static/rest_framework_swagger static/

$GAE_DIR/google_appengine/appcfg.py \
    --oauth2_refresh_token=$REFRESH_TOKEN \
    update .
