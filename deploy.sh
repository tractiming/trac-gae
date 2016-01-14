#!/bin/bash

# This script installs all the Python dependencies that need to
# be vendored into the application, then pushes the code to
# AppEngine.

rm -rf libs
mkdir libs
echo 'Deleted existing libs...'

pip freeze | xargs pip uninstall -y
pip install \
    --no-deps \
    --upgrade \
    --force-reinstall \
    --install-option="--prefix=$(pwd)/libs" \
    -r requirements/production.txt
echo 'Pip installed dependencies...'

if [ -d libs ]; then
    cd libs
    mv lib/python2.7/site-packages/* .
    rm -rf lib
    rm -rf bin

    # AppEngine will not upload both .py and .pyc versions of a
    # file. Also note that gcloud requires us to keep the
    # .egg-info files around :/
    find . -name "*.pyc" -delete
    find . -name "*.egg-info" -not -name "*gcloud*" | xargs rm -rf

    # Delete some locale files to stay under the file limit.
    rm -rf django/contrib/admin/locale/*

    # If needed, we can zip some of the packages and then have
    # AppEngine use zipimport. Not all modules can be zipped.
    # For instance, Django has non .py locale files that need
    # to be imported, and other packages have migrations in
    # places that are expected to be unzipped directories.
    #zip -9mrv libs.zip . -x \
    #    django/\* \
    #    oauth2_provider/\* \
    #    djstripe/\* \
    #    *.egg-info/\*
    #
    cd ..
    ls -l
    ls -l libs
fi
echo 'Created zip archive...'

cp -r libs/django/contrib/admin/static/admin static/

# Push changed to AppEngine.
$GAE_DIR/google_appengine/appcfg.py \
    --oauth2_refresh_token=$REFRESH_TOKEN \
    update .
