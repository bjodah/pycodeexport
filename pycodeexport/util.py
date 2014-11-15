# -*- coding: utf-8 -*-
from __future__ import (
    print_function, division, absolute_import, unicode_literals
)

import os

from collections import namedtuple, OrderedDict

from pycompilation.util import (
    md5_of_file, missing_or_other_newer, get_abspath, make_dirs
)


def render_mako_template_to(
        template, outpath, subsd, only_update=False, cwd=None,
        prev_subsd=None, create_dest_dirs=False, logger=None,
        pass_warn_string=True, **kwargs):
    """
    template: either string of path or file like obj.

    Beware of the only_update option, it pays no attention to
    an updated subsd.

    pass_warn_string: defult True
    if True or instance of basetring:
    an extra vairable named '_warning_in_the_generated_file_not_to_edit'
    is passed with a preset (True) or string (basestring) warning not to
    directly edit the generated file.
    """
    if cwd:
        template = os.path.join(cwd, template)
        outpath = os.path.join(cwd, outpath)
    outdir = os.path.dirname(outpath) or '.'  # avoid ''

    if not os.path.exists(outdir):
        if create_dest_dirs:
            make_dirs(outdir, logger=logger)
        else:
            raise FileNotFoundError(
                "Dest. dir. non-existent: {}".format(outdir))

    msg = None
    if pass_warn_string is True:
        subsd['_warning_in_the_generated_file_not_to_edit'] = (
            "DO NOT EDIT THIS FILE! (Generated from template: {} using" +
            " Mako python templating engine)"
        ).format(os.path.basename(template))
    elif isinstance(pass_warn_string, basestring):
        subsd['_warning_in_the_generated_file_not_to_edit'] =\
            pass_warn_string

    if only_update:
        if prev_subsd == subsd and not \
           missing_or_other_newer(outpath, template):
            if logger:
                msg = "Did not re-render {}. (destination newer + same dict)"
                logger.info(msg.format(template))
            return

    if hasattr(template, 'read'):
        # set in-file handle to provided template
        ifh = template
    else:
        # Assume template is a string of the path to the template
        ifh = open(template, 'rt')

    template_str = ifh.read()

    kwargs_Template = {'input_encoding': 'utf-8', 'output_encoding': 'utf-8'}
    kwargs_Template.update(kwargs)
    with open(outpath, 'wb') as ofh:
        from mako.template import Template
        from mako.exceptions import text_error_template
        try:
            rendered = Template(
                template_str, **kwargs_Template).render(**subsd)
        except:
            if logger:
                logger.error(text_error_template().render())
            else:
                print(text_error_template().render())
            raise
        if logger:
            logger.info("Rendering '{}' to '{}'...".format(
                ifh.name, outpath))
        ofh.write(rendered)
    return outpath


def download_files(websrc, files, md5sums, cwd=None,
                   only_if_missing=True, logger=None):
    dest_paths = []
    for f in files:
        fpath = os.path.join(cwd, f) if cwd else f
        if not os.path.exists(fpath):
            import urllib2
            msg = 'Downloading: {0}'.format(websrc+f)
            if logger:
                logger.info(msg)
            else:
                print(msg)
            open(fpath, 'wt').write(urllib2.urlopen(websrc+f).read())
        fmd5 = md5_of_file(fpath).hexdigest()
        if fmd5 != md5sums[f]:
            raise ValueError(("Warning: MD5 sum of {0} differs from "
                             "that provided in setup.py. i.e. {1} "
                             "vs. {2}").format(f, fmd5, md5sums[f]))
        dest_paths.append(get_abspath(fpath, cwd=cwd))
    return dest_paths


def defaultnamedtuple(name, args, defaults=(), typing=()):
    """
    defaultnamedtuple returns a new subclass of Tuple with named fields
    and a constructor with implicit default values.

    Parameters
    ==========
    name: string
         the name of the class
    args: tuple
        a tuple or a splitable string
    defaults: iterable
        default values for args, counting [-len(defaults):]
    typing`: iterable of callbacks
        optional requirements for type, counting [:len(typing)]
        should be an iterable of callbacks returning True for
        conformance.

    Examples
    ========
    >>> Body = namedtuple('Body', 'x y z density', (1.0,))
    >>> Body.__doc__
    SOMETHING
    >>> b = Body(10, z=3, y=5)
    >>> b._asdict()
    {'density': 1.0, 'x': 10, 'y': 5, 'z': 3}

    """
    nt = namedtuple(name, args)
    kw_order = args.split() if isinstance(args, (str, bytes)) else args
    nargs = len(kw_order)

    # Sanity check that `defaults` conform to typing
    if len(typing) + len(defaults) > nargs:
        # there is an overlap
        noverlap = len(typing) + len(defaults) - nargs
        for i, t in enumerate(typing[-noverlap:]):
            assert t(defaults[i])

    # We will be returning a factory which intercepts before
    # calling our namedtuple constructor
    def factory(*args, **kwargs):
        # Set defaults for missing args
        n_missing = nargs-len(args)
        if n_missing > 0:
            unset = OrderedDict(zip(kw_order[-n_missing:],
                                    defaults[-n_missing:]))
            unset.update(kwargs)
            args += tuple(unset.values())

        # Type checking
        for i, t in enumerate(typing):
            if not t(args[i]):
                raise ValueError(
                    'Argument {} ({}) does not conform to' +
                    ' typing requirements'.format(i, args[i]))
        # Construct namedtuple instance and return it
        return nt(*args)
    factory.__doc__ = nt.__doc__
    return factory
