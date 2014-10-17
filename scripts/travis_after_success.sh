#!/bin/bash
set -x # Verbose
MINICONDA_HOME=$1

GH_USER=bjodah
GH_REPO=pycodeexport
BINSTAR_USER=$GH_USER
if [ "$TRAVIS_REPO_SLUG" == "${GH_USER}/${GH_REPO}" ] && [ "$TRAVIS_PULL_REQUEST" == "false" ] && [ "$TRAVIS_BRANCH" == "master" ]; then
    # Push wheel to binstar.org (for all Python versions)
    conda config --add channels http://conda.binstar.org/$BINSTAR_USER
    conda install conda-build jinja2 binstar
    conda build conda-recipe/
    set +x # Silent  (protect token in Travis log)
    echo "Uploading to binstar..."
    binstar -t ${BINSTAR_TOKEN} upload --force $MINICONDA_HOME/conda-bld/linux-64/*.tar.bz2
fi
