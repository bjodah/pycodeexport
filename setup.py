#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from distutils.core import setup

pkg_name = 'pycodeexport'
exec(open(pkg_name + '/release.py').read())

CONDA_BUILD = os.environ.get('CONDA_BUILD', '0') == '1'
if CONDA_BUILD:
    open('__conda_version__.txt', 'w').write(__version__)

classifiers = [
    "Development Status :: 2 - Pre-Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Operating System :: POSIX",
    "Programming Language :: Python",
    "Programming Language :: C",
    "Programming Language :: C++",
    "Programming Language :: Cython",
    "Programming Language :: Fortran",
    "Topic :: Software Development :: Code Generators",
    "Topic :: Software Development :: Compilers",
    "Topic :: Software Development :: Libraries :: Python Modules"
]

setup_kwargs = dict(
    name=pkg_name,
    version=__version__,
    author='Björn Dahlgren',
    author_email='bjodah@DELETEMEgmail.com',
    description='Python package for codegeneration.',
    license="BSD",
    url='https://github.com/bjodah/'+pkg_name,
    download_url=('https://github.com/bjodah/' + pkg_name +
                  '/archive/v' + __version__ + '.tar.gz'),
    packages=[pkg_name],
    classifiers=classifiers
)

if __name__ == '__main__':
    setup(**setup_kwargs)
