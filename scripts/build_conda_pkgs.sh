#!/bin/bash -x

# Extract absolute path of script, from:
# http://unix.stackexchange.com/a/9546
# Note: we are assuming this script is inside a subdirectory of the repo root
absolute_repo_path_x="$(readlink -fn -- "$(dirname $0)/.."; echo x)"
absolute_repo_path="${absolute_repo_path_x%x}"

if [[ ! -e build ]]; then
    mkdir build
else
    if [ "$(ls -A build/)" ]; then
        rm -r build/*
    fi
fi
cd build/
for CONDA_PY in {27,34}; do
    echo $CONDA_PY
    echo ========================
    CONDA_PY=$CONDA_PY conda build ${absolute_repo_path}/conda-recipe
    conda convert -p all $(CONDA_PY=$CONDA_PY conda build --output ${absolute_repo_path}/conda-recipe)
done
