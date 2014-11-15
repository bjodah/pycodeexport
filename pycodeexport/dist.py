# -*- coding: utf-8 -*-

"""
Transition module. Deprecated.
"""


from pycompilation.dist import (
    PCExtension, pc_build_ext
)

from .util import render_mako_template_to


def PCEExtension(*args, **kwargs):
    return PCExtension(*args, **kwargs)


class pce_build_ext(pc_build_ext):
    """
    build_ext class for PCEExtension
    Support for template_regexps
    """
    def render_template_to(self, *args, **kwargs):
        render_mako_template_to(*args, **kwargs)
