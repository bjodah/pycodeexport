# -*- coding: utf-8 -*-

"""
Interaction with distutils
"""

import os
import re

from distutils.command import build_ext
from distutils.extension import Extension

from pycompilation.compilation import (
    extension_mapping, FortranCompilerRunner, CppCompilerRunner,
    compile_sources, link_py_so, any_fort,
    any_cplus
)
from .pycompilation.util import (
    copy, get_abspath, import_module_from_file,
    MetaReaderWriter, FileNotFoundError
)

from .util import render_mako_template_to


def CleverExtension(*args, **kwargs):
    """
    Parameters
    ==========
    template_regexps: list of 3-tuples
        e.g. [(pattern1, target1, subsd1), ...], used to generate
        templated code
    pass_extra_compile_args: bool
        should ext.extra_compile_args be passed along? default: False
    """
    vals = {}

    intercept = {
        'build_callbacks': (),  # tuple of (callback, args, kwargs)
        'link_ext': True,
        'build_files': (),
        'dist_files': (),  # work around stackoverflow.com/questions/2994396/
        'template_regexps': [],
        'pass_extra_compile_args': False,  # use distutils extra_compile_args?
        'pycompilation_compile_kwargs': {},
        'pycompilation_link_kwargs': {},
    }
    for k, v in intercept.items():
        vals[k] = kwargs.pop(k, v)

    intercept2 = {
        'logger': None,
        'only_update': True,
    }
    for k, v in intercept2.items():
        vck = kwargs.pop(k, v)
        vck = vals['pycompilation_compile_kwargs'].pop(k, vck)
        vck = vck or vals['pycompilation_link_kwargs'].pop(k, vck)
        vals[k] = vck

    instance = Extension(*args, **kwargs)

    if vals['logger'] is True:
        # interpret as we should instantiate a logger
        import logging
        logging.basicConfig(level=logging.DEBUG)
        vals['logger'] = logging.getLogger('CleverExtension')

    for k, v in vals.items():
        setattr(instance, k, v)

    return instance


class clever_build_ext(build_ext.build_ext):
    """
    build_ext class for CleverExtension
    Support for template_regexps
    """
    def _copy_or_render_source(self, ext, f):
        # Either render a template or copy the source
        dirname = os.path.dirname(f)
        filename = os.path.basename(f)
        for pattern, target, subsd in ext.template_regexps:
            if re.match(pattern, filename):
                tgt = os.path.join(dirname, re.sub(
                    pattern, target, filename))
                rw = MetaReaderWriter('.metadata_subsd')
                try:
                    prev_subsd = rw.get_from_metadata_file(self.build_temp, f)
                except (FileNotFoundError, KeyError):
                    prev_subsd = None

                render_mako_template_to(
                    get_abspath(f),
                    os.path.join(self.build_temp, tgt),
                    subsd,
                    only_update=ext.only_update,
                    prev_subsd=prev_subsd,
                    create_dest_dirs=True,
                    logger=ext.logger)
                rw.save_to_metadata_file(self.build_temp, f, subsd)
                return tgt
        else:
            copy(f,
                 os.path.join(self.build_temp,
                              os.path.dirname(f)),
                 only_update=ext.only_update,
                 dest_is_dir=True,
                 create_dest_dirs=True,
                 logger=ext.logger)
            return f

    def run(self):
        if self.dry_run:
            return  # honor the --dry-run flag
        for ext in self.extensions:
            sources = []
            if ext.logger:
                ext.logger.info("Copying/rendering sources...")
            for f in ext.sources:
                sources.append(self._copy_or_render_source(ext, f))

            if ext.logger:
                ext.logger.info("Copying build_files...")
            for f in ext.build_files:
                copy(f, os.path.join(self.build_temp,
                                     os.path.dirname(f)),
                     only_update=ext.only_update,
                     dest_is_dir=True,
                     create_dest_dirs=True,
                     logger=ext.logger)

            if ext.pass_extra_compile_args:
                # By default we do not pass extra_compile_kwargs
                # since it contains '-fno-strict-aliasing' which
                # harms performance.
                ext.pycompilation_compile_kwargs['flags'] =\
                    ext.extra_compile_args,
            if ext.define_macros:
                ext.pycompilation_compile_kwargs['defmacros'] =\
                    list(set(ext.define_macros +
                             ext.pycompilation_compile_kwargs['defmacros']))
            if ext.undef_macros:
                ext.pycompilation_compile_kwargs['undefmacros'] =\
                    list(set(ext.undef_macros +
                             ext.pycompilation_compile_kwargs['undefmacros']))

            # Run build_callbaks if any were provided
            for cb, args, kwargs in ext.build_callbacks:
                cb(self.build_temp, self.get_ext_fullpath(
                    ext.name), ext, *args, **kwargs)

            # Compile sources to object files
            src_objs = compile_sources(
                sources,
                cwd=self.build_temp,
                inc_dirs=map(get_abspath, ext.include_dirs),
                lib_dirs=map(get_abspath, ext.library_dirs),
                libs=ext.libraries,
                logger=ext.logger,
                only_update=ext.only_update,
                **ext.pycompilation_compile_kwargs
            )

            if ext.logger:
                ext.logger.info(
                    "Copying files needed for distribution..")
            for f, rel_dst in ext.dist_files:
                rel_dst = rel_dst or os.path.basename(f)
                copy(
                    f,
                    os.path.join(
                        os.path.dirname(self.get_ext_fullpath(ext.name)),
                        rel_dst,
                    ),
                    only_update=ext.only_update,
                    logger=ext.logger,
                )

            # Link objects to a shared object
            if ext.link_ext:
                abs_so_path = link_py_so(
                    src_objs+ext.extra_objects,
                    cwd=self.build_temp,
                    flags=ext.extra_link_args,
                    fort=any_fort(sources),
                    cplus=(((ext.language or '').lower() == 'c++') or
                           any_cplus(sources)),
                    logger=ext.logger,
                    only_update=ext.only_update,
                    **ext.pycompilation_link_kwargs
                )
                copy(
                    abs_so_path, self.get_ext_fullpath(ext.name),
                    only_update=ext.only_update,
                    create_dest_dirs=True, logger=ext.logger
                )
