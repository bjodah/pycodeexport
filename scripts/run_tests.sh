#!/bin/bash -e
# Usage
#   $ ./scripts/run_tests.sh
# or
#   $ ./scripts/run_tests.sh --cov pycvodes --cov-report html
${PYTHON:-python3} -m pytest --doctest-modules "$@" # --flake8
python3 -m doctest README.rst
