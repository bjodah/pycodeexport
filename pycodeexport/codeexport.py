# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

"""
When a Sympy expressions needs to be evaluated it is,
for performance reasons, preferable that the
numerics are performed in a compiled language
the codeexport module provide classes enabling
templates to be used as blueprints for generating, compiling
and importing a binary which performs the computations.


Both C, C++ and Fortran is considered, but since
the codegeneration uses templates, one can easily extend
the functionality to other languages.

The approach taken here differs from sympy.utilities.codegen.codegen
through the use of Mako templates and classes which controlls
the how they are rendered. Which method is best depends on
the problem at hand (personal opinion).
"""

# stdlib imports
import tempfile
import shutil
import re
import os

from collections import namedtuple
from functools import partial

# External imports
import sympy
from pycompilation.util import (
    import_module_from_file, copy, make_dirs
)
from pycompilation.compilation import (
    FortranCompilerRunner, CCompilerRunner,
    CppCompilerRunner, link_py_so, compile_sources
)

# Intrapackage imports
from .util import render_mako_template_to, download_files, defaultnamedtuple

Loop = namedtuple('Loop', ('counter', 'bounds', 'body'))

# DummyGroup instances are used in transformation from sympy expression
# into code. It is used to protect symbols from being operated upon.
DummyGroup = namedtuple('DummyGroup', 'basename symbols')

# ArrayifyGroup instances defines what expressions should be
# arrayified and what offset should be used
# arg `dim` is for broadcasting (Fortran)
ArrayifyGroup = defaultnamedtuple(
    'ArrayifyGroup', 'basename code_tok offset dim', [None, 0])


def _dummify_expr(expr, basename, symbs):
    """
    Useful to robustify prior to e.g. regexp substitution of
    code strings
    """
    dummies = sympy.symbols(basename+':'+str(len(symbs)))
    for i, s in enumerate(symbs):
        expr = expr.subs({s: dummies[i]})
    return expr


def syntaxify_getitem(syntax, scode, basename, token, offset=None,
                      dim=0, match_regex='(\d+)'):
    """

    Parameters
    ----------
    syntax : str
        Either 'C' or 'F' for C or Fortran respectively
    scode: str
        Code string to transformed.
    basename : str
        Name of (array) variable in scode.
    token: str
        Name of (array) variable in code.

    Examples
    --------
    >>> syntaxify_getitem('C', 'y_i = x_i+i;', 'y', 'yout',
    ...     offset='CONST', match_regex=r'_(\w)')
    'yout[i+CONST] = x_i+i;'

    >>> syntaxify_getitem('F', 'y7 = x7+i;', 'y', 'yout',
    ...     offset=-3, dim=-1)
    'yout(7-3,:) = x7+i;'

    """
    if syntax == 'C':
        assert dim == 0  # C does not support broadcasting
    if isinstance(offset, int):
        offset_str = '{0:+d}'.format(offset)
    elif offset is None:
        offset_str = ''
    else:
        offset_str = '+'+str(offset)

    c_tgt = token+r'[\1'+offset_str+']'
    if dim > 0:
        f_tgt = token+'('+':,'*dim+r'\1'+offset_str+')'  # slow!
    else:
        f_tgt = token+'('+r'\1'+offset_str+',:'*-dim+')'  # fast!
    tgt = {'C': c_tgt, 'F': f_tgt}.get(syntax)
    return re.sub(basename+match_regex, tgt, scode)


class Interceptor(object):
    """
    This is a wrapper for dynamically loaded extension modules
    which share the same name (they end up overwriting the same
    python object).
    """

    def __init__(self, binary_path):
        self._binary_path = binary_path
        self._binary_mod = import_module_from_file(self._binary_path)

    def __getattr__(self, key):
        if key == '__file__':
            return self._binary_mod.__file__

        if self._binary_mod.__file__ != self._binary_path:
            # Avoid singleton behaviour. (Python changes binary path
            # inplace without changing id of Python object)
            self._binary_mod = import_module_from_file(self._binary_path)
        return getattr(self._binary_mod, key)


class Generic_Code(object):
    """ Base class representing code generating object.

    Attributes
    ----------
    syntax : str
        Any of the supported syntaxes ('C' or 'F').
    tempdir_basename:  basename of tempdirs created in e.g. /tmp/
    basedir : str
        The path to the directory which relative (source).

    Notes
    -----
    Regarding syntax:
        - C99 is assumed for 'C'
        - Fortran 2008 (free form) is assumed for 'F'

    """

    CompilerRunner = None  # Set to compilation.CompilerRunner subclass

    syntax = None
    fort = False  # a form of fortran code? (decisive for linking)
    tempdir_basename = 'generic_code'
    basedir = None
    _cached_files = None
    build_files = None
    source_files = None
    templates = None
    obj_files = None
    extension_name = 'generic_extension'
    so_file = None
    extension_name = None
    compile_kwargs = None  # kwargs passed to CompilerRunner

    list_attributes = (
        '_written_files',  # Track what files are written
        'build_files',   # Files to be copied prior to compilation
        'source_files',
        'templates',
        'obj_files',
        '_cached_files',  # Files to be removed between compilations
    )

    def __init__(self, tempdir=None, save_temp=False, logger=None):
        """
        Arguments:
        - `tempdir`: Optional path to dir to write code files
        - `save_temp`: Save generated code files when garbage
            collected? (Default: False)
        - `logger`: optional logging.Logger instance.
        """

        if self.syntax == 'C':
            self.wcode = partial(sympy.ccode, contract=False)
        elif self.syntax == 'F':
            self.wcode = partial(
                sympy.fcode, source_format='free', contract=False)

        self.basedir = self.basedir or "."
        # setting basedir to:
        # os.path.dirname(sys.modules[self.__class__.__module__].__file__)
        # gives problems when using e.g. pudb.

        if tempdir:
            self._tempdir = tempdir
            self._remove_tempdir_on_clean = False
        else:
            self._tempdir = tempfile.mkdtemp(self.tempdir_basename)
            self._remove_tempdir_on_clean = True
        self._save_temp = save_temp

        self.logger = logger

        if not os.path.isdir(self._tempdir):
            os.makedirs(self._tempdir)
            self._remove_tempdir_on_clean = True

        # Initialize lists
        for lstattr in self.list_attributes:
            setattr(self, lstattr, getattr(
                self, lstattr, None) or [])

        self.compile_kwargs = self.compile_kwargs or {}

        # If .pyx files in self.templates, add .c file to _cached_files
        self._cached_files += [x.replace('_template', '').replace(
            '.pyx', '.c') for x in self.templates if x.endswith('.pyx')]

        self.write_code()

    def variables(self):
        """
        Returns dictionary of variables for substituion
        suitable for use in the templates (formated according
        to the syntax of the language)
        """
        # To be overloaded
        return {}

    def as_arrayified_code(self, expr, dummy_groups=(),
                           arrayify_groups=(), **kwargs):
        for basename, symbols in dummy_groups:
            expr = _dummify_expr(expr, basename, symbols)

        scode = self.wcode(expr, **kwargs)

        for basename, code_tok, offset, dim in arrayify_groups:
            scode = syntaxify_getitem(
                self.syntax, scode, basename, code_tok, offset, dim)
        return scode

    def get_cse_code(self, exprs, basename=None,
                     dummy_groups=(), arrayify_groups=()):
        """ Get arrayified code for common subexpression.

        Parameters
        ----------
        exprs : list of sympy expressions
        basename : str
            Stem of variable names (default: cse).
        dummy_groups : tuples

        """
        if basename is None:
            basename = 'cse'
        cse_defs, cse_exprs = sympy.cse(
            exprs, symbols=sympy.numbered_symbols(basename))

        # Let's convert the new expressions into (arrayified) code
        cse_defs_code = [
            (vname, self.as_arrayified_code(
                vexpr, dummy_groups, arrayify_groups))
            for vname, vexpr in cse_defs
        ]
        cse_exprs_code = [self.as_arrayified_code(
            x, dummy_groups, arrayify_groups) for x in cse_exprs]
        return cse_defs_code, cse_exprs_code

    def write_code(self):
        for path in self._cached_files:
            # Make sure we start in a clean state
            rel_path = os.path.join(self._tempdir, path)
            if os.path.exists(rel_path):
                os.unlink(rel_path)
        for path in self.build_files:
            # Copy files
            srcpath = os.path.join(self.basedir, path)
            dstpath = os.path.join(self._tempdir, os.path.basename(path))
            copy(srcpath, dstpath)
            self._written_files.append(dstpath)

        subs = self.variables()
        for path in self.templates:
            # Render templates
            srcpath = os.path.join(self.basedir, path)
            outpath = os.path.join(
                self._tempdir,
                os.path.basename(path).replace('_template', ''))
            render_mako_template_to(srcpath, outpath, subs)
            self._written_files.append(outpath)

    _mod = None

    @property
    def mod(self):
        """ Cached compiled binary of the Generic_Code class.

        To clear cache invoke :meth:`clear_mod_cache`.
        """
        if self._mod is None:
            self._mod = self.compile_and_import_binary()
        return self._mod

    def clear_mod_cache(self):
        self._mod = None

    def compile_and_import_binary(self):
        """
        Returnes a module instance of the extension module.
        Consider using the `mod` property instead.

        Do ::
        >>> mod = codeinstnc.compile_and_import_binary()  # doctest: +SKIP
        >>> x = mod.cb('foo') # doctest: +SKIP

        Don't ::
        >>> cb = codeinstnc.compile_and_import_binary().cb  # doctest: +SKIP

        Since that circumvents measurments avoiding singleton
        behaviour when multiple different versions of the same
        extension module have been compiled. (the shared object
        has the same name and identifier)
        """
        self._compile()
        return Interceptor(self.binary_path)

    @property
    def binary_path(self):
        return os.path.join(self._tempdir, self.so_file)

    def clean(self):
        """ Delete temp dir if not save_temp set at __init__ """
        if not self._save_temp:
            map(os.unlink, self._written_files)
            if self._remove_tempdir_on_clean:
                shutil.rmtree(self._tempdir)

    def __del__(self):
        """
        When Generic_Code object is collected by GC
        self._tempdir is (possibly) deleted
        """
        self.clean()

    def _compile(self):
        self._compile_obj()
        self._compile_so()

    def _compile_obj(self, sources=None):
        sources = sources or self.source_files
        compile_sources(sources, self.CompilerRunner,
                        cwd=self._tempdir,
                        logger=self.logger,
                        **self.compile_kwargs)

    def _compile_so(self):
        so_file = link_py_so(self.obj_files,
                             so_file=self.so_file,
                             cwd=self._tempdir,
                             fort=self.fort,
                             logger=self.logger,
                             **self.compile_kwargs)
        self.so_file = self.so_file or so_file


class Cython_Code(Generic_Code):
    """
    Uses Cython's build_ext and distutils
    to simplify compilation

    Could be rewritten to use pyx2obj
    """

    def _compile(self):
        from Cython.Distutils import build_ext
        from setuptools import setup
        from setuptools import Extension

        sources = [os.path.join(
            self._tempdir, os.path.basename(x).replace(
                '_template', '')) for x in self.source_files]
        setup(
            script_name='DUMMY_SCRIPT_NAME',
            script_args=['build_ext',  '--build-lib', self._tempdir],
            include_dirs=self._include_dirs,
            cmdclass={'build_ext': build_ext},
            ext_modules=[
                Extension(
                    self.extension_name,
                    sources,
                    libraries=self._libraries,
                    library_dirs=self._library_dirs,
                    include_dirs=self._include_dirs),
                ]
            )


class C_Code(Generic_Code):
    """
    C code class
    """

    default_integer = 'int'
    default_real = 'double'

    syntax = 'C'
    CompilerRunner = CCompilerRunner


class Cpp_Code(C_Code):
    CompilerRunner = CppCompilerRunner


class F90_Code(Generic_Code):
    """
    Fortran 90 code class
    """

    fort = True

    # Assume `use iso_c_binding`
    default_integer = 'integer(c_int)'
    default_real = 'real(c_double)'

    syntax = 'F'
    CompilerRunner = FortranCompilerRunner

    def __init__(self, *args, **kwargs):
        self._cached_files = self._cached_files or []
        # self._cached_files += [
        #  x+'.mod' for x in self._get_module_files(self.source_files)]
        self._cached_files += [
            x+'.mod' for x in self._get_module_files(self.templates)]
        super(F90_Code, self).__init__(*args, **kwargs)

    def _get_module_files(self, files):
        names = []
        for f in files:
            with open(os.path.join(self.basedir, f), 'rt') as fh:
                for line in fh:
                    stripped_lower = line.strip().lower()
                    if stripped_lower.startswith('module'):
                        names.append(
                            stripped_lower.split('module')[1].strip())
        return names


def make_PCEExtension_for_prebuilding_Code(
        name, Code, prebuild_sources, srcdir,
        downloads=None, **kwargs):
    """
    If subclass of codeexport.Generic_Code needs to have some of it
    sources compiled to objects and cached in a `prebuilt/` directory
    at invocation of `setup.py build_ext` this convenience function
    makes setting up a PCEExtension easier. Use together with
    cmdclass = {'build_ext': pce_build_ext}.

    files called ".metadata*" will be added to dist_files
    """

    import glob
    from .dist import PCEExtension

    build_files = []
    dist_files = [(os.path.join(srcdir, x[0]), x[1]) for
                  x in getattr(Code, 'dist_files', [])]
    for attr in ('build_files', 'templates'):
        for cf in getattr(Code, attr, []) or []:
            if not cf.startswith('prebuilt'):
                build_files.append(os.path.join(srcdir, cf))
                dist_files.append((os.path.join(srcdir, cf), None))

    def prebuilder(build_temp, ext_fullpath, ext,
                   src_paths, **prebuilder_kwargs):
        build_temp = os.path.abspath(build_temp)
        if not os.path.isdir(build_temp):
            make_dirs(build_temp)

        if downloads:
            websrc, src_md5 = downloads
            download_dir = os.path.join(build_temp, srcdir)
            if not os.path.isdir(download_dir):
                make_dirs(download_dir)
            download_files(websrc, src_md5.keys(), src_md5,
                           cwd=download_dir, logger=ext.logger)

        for p in src_paths:
            if p not in build_files:
                copy(os.path.join(srcdir, p),
                     os.path.join(build_temp, srcdir),
                     dest_is_dir=True, create_dest_dirs=True,
                     only_update=ext.only_update,
                     logger=ext.logger)
        dst = os.path.abspath(os.path.join(
            os.path.dirname(ext_fullpath), 'prebuilt/'))
        make_dirs(dst, logger=ext.logger)
        objs = compile_sources(
            [os.path.join(srcdir, x) for x in src_paths], destdir=dst,
            cwd=build_temp, metadir=dst, only_update=True,
            logger=ext.logger, **prebuilder_kwargs)
        glb = os.path.join(ext_fullpath, '.metadata*')
        dist_files.extend(glob.glob(glb))
        for obj in objs:
            # Copy prebuilt objects into lib for distriubtion
            copy(os.path.join(build_temp, obj),
                 dst, dest_is_dir=True, create_dest_dirs=True,
                 only_update=ext.only_update,
                 logger=ext.logger)
        return objs

    compile_kwargs = Code.compile_kwargs.copy()
    logger = kwargs.pop('logger', True)
    compile_kwargs.update(kwargs)
    return PCEExtension(
        name,
        [],
        build_files=build_files,
        dist_files=dist_files,
        build_callbacks=[
            (
                prebuilder,
                (prebuild_sources,), compile_kwargs
            ),
        ],
        logger=logger,
        link_ext=False
    )
