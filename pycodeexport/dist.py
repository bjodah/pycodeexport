# -*- coding: utf-8 -*-

"""
Transition module. Deprecated.
"""


from pycompilation.dist import (
    PCExtension, pc_build_ext, pc_sdist
)

from .util import render_mako_template_to


def PCEExtension(*args, **kwargs):
    return PCExtension(*args, **kwargs)


class pce_build_ext(pc_build_ext):
    """
    build_ext class for PCEExtension
    """
    render_callback = staticmethod(render_mako_template_to)


class pce_sdist(pc_sdist):
    """
    sdist class for PCEExtension
    """
    render_callback = staticmethod(render_mako_template_to)
