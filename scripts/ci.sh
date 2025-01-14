#!/bin/bash
set -euxo pipefail
PKG_NAME=${1:-${CI_REPO##*/}}
if [[ "${CI_COMMIT_BRANCH:-}" =~ ^v[0-9]+.[0-9]?* ]]; then
    eval export ${PKG_NAME^^}_RELEASE_VERSION=\$CI_COMMIT_BRANCH
fi
source $(compgen -G /opt-3/cpython-v3.*-apt-deb/bin/activate)
( set -e; python -c "import pycompilation" || pip install "git+https://github.com/bjodah/pycompilation@use-importlib-rather-than-imp#egg=pycompilation" )
python3 setup.py sdist
(cd dist/; python3 -m pip install pytest $PKG_NAME-$(python3 ../setup.py --version).tar.gz)
(cd /; python3 -m pytest --pyargs $PKG_NAME)
python3 -m pip install .[all]
PYTHONPATH=$(pwd) PYTHON=python3 ./scripts/run_tests.sh --cov $PKG_NAME --cov-report html -v
./scripts/coverage_badge.py htmlcov/ htmlcov/coverage.svg
! grep "DO-NOT-MERGE!" -R . --exclude ci.sh
