#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import shutil
from setuptools import setup

pkg_name = 'pycodeexport'

RELEASE_VERSION = os.environ.get('%s_RELEASE_VERSION' % pkg_name.upper(), '')

# http://conda.pydata.org/docs/build.html#environment-variables-set-during-the-build-process
if os.environ.get('CONDA_BUILD', '0') == '1':
    try:
        RELEASE_VERSION = 'v' + io.open(
            '__conda_version__.txt', 'rt', encoding='utf-8'
        ).readline().rstrip()
    except IOError:
        pass


def _path_under_setup(*args):
    return os.path.join(os.path.dirname(__file__), *args)

release_py_path = _path_under_setup(pkg_name, '_release.py')

if (len(RELEASE_VERSION) > 1 and RELEASE_VERSION[0] == 'v'):
    TAGGED_RELEASE = True
    __version__ = RELEASE_VERSION[1:]
else:
    TAGGED_RELEASE = False
    # read __version__ attribute from _release.py:
    exec(io.open(release_py_path, encoding='utf-8').read())

tests = [
    '%s.tests' % pkg_name,
]


classifiers = [
    "Development Status :: 3 - Alpha",
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

with io.open(_path_under_setup(pkg_name, '__init__.py'), 'rt',
             encoding='utf-8') as f:
    short_description = f.read().split('"""')[1].split('\n')[1]
assert 10 < len(short_description) < 255
long_descr = io.open(_path_under_setup('README.rst'), encoding='utf-8').read()
assert len(long_descr) > 100


setup_kwargs = dict(
    name=pkg_name,
    version=__version__,
    author='Björn Dahlgren',
    author_email='bjodah@DELETEMEgmail.com',
    description=short_description,
    long_description=long_descr,
    license="BSD",
    packages=[pkg_name] + tests,
    install_requires=['mako>=1.0.0', 'pycompilation>=0.4.0', 'sympy>=0.7.5',
                      'cython>=0.20.2'],
    extras_require={
        'all': ['cython', 'pytest', 'numpy', 'Sphinx', 'sphinx_rtd_theme',
                'numpydoc', 'pytest-cov', 'pytest-flakes', 'pytest-pep8']
    },
    classifiers=classifiers,
)

if __name__ == '__main__':
    try:
        if TAGGED_RELEASE:
            # Same commit should generate different sdist
            # depending on tagged version (set ${pkg_name}_RELEASE_VERSION)
            # this will ensure source distributions contain the correct version
            shutil.move(release_py_path, release_py_path+'__temp__')
            open(release_py_path, 'wt').write(
                "__version__ = '{}'\n".format(__version__))
        setup(**setup_kwargs)
    finally:
        if TAGGED_RELEASE:
            shutil.move(release_py_path+'__temp__', release_py_path)
