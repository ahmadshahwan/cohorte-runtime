#!/bin/bash

DEVPI_URL=$1
devpi_index=$2
devpi_user=$3
devpi_password=$4
devpi_formats=$5

# Move to the Python sources
cd python

# Set up the virtual environment
VENV_NAME=venv
rm -fr $VENV_NAME
virtualenv $VENV_NAME -p python3 || return 1
PATH=$WORKSPACE/$VENV_NAME/bin:$PATH
. $VENV_NAME/bin/activate

# Install test and deployment tools
pip install --force --upgrade pip==1.5.6 setuptools || return 2
pip install --upgrade wheel || return 2
pip install --upgrade nose || return 2
pip install --upgrade devpi-client || return 2

# Install project
pip install .

# Run tests
# nosetests tests || return 3

# Deploy
devpi use $DEVPI_URL
devpi login $devpi_user --password=$devpi_password
devpi use $devpi_index
devpi upload --no-vcs --formats=$devpi_formats

# Clean up
deactivate
rm -fr $VENV_NAME