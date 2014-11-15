#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from distutils.core import setup

pkg_name = 'pycodeexport'
pkg_version = '0.1.0.dev'
pkg_is_released = False

if os.environ.get('CONDA_BUILD', None):
    with open('__conda_version__.txt', 'w') as f:
        if pkg_is_released:
            f.write(pkg_version)
        else:
            f.write(pkg_version + '.dev')

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

setup(
    name=pkg_name,
    version=pkg_version,
    author='Björn Dahlgren',
    author_email='bjodah@DELETEMEgmail.com',
    description='Python package for codegeneration.',
    license="BSD",
    url='https://github.com/bjodah/'+pkg_name,
    download_url=('https://github.com/bjodah/' + pkg_name +
                  '/archive/v' + pkg_version + '.tar.gz'),
    packages=[pkg_name],
    classifiers=classifiers
)
