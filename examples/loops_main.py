#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict
import os

import numpy as np
import sympy

from pycodeexport.codeexport import C_Code, Loop


def get_idxs(exprs):
    """
    Finds sympy.tensor.indexed.Idx instances and returns them.
    """
    idxs = set()
    for expr in (exprs):
        for i in expr.find(sympy.Idx):
            idxs.add(i)
    return sorted(idxs, key=str)


class ExampleCode(C_Code):
    """
    Render _arbitrary_func to do loops
    """

    basedir = os.path.dirname(__file__)
    templates = ['loops_template.c']
    source_files = ['loops.c',
                    'loops_wrapper.pyx']
    compile_kwargs = {
        'std': 'c99',
        'libraries': ['m'],
        'include_dirs': [np.get_include()]
    }
    build_files = ['loops_wrapper.pyx']
    obj_files = [
        'loops.o',
        'loops_wrapper.o',
    ]

    def __init__(self, eqs, inputs, indices, **kwargs):
        self.unk = [x.lhs for x in eqs]
        self.exprs = [x.rhs for x in eqs]
        self.inputs = inputs
        self.indices = indices
        assert get_idxs(self.exprs) == sorted(
            indices, key=str)  # sanity check

        # list of lists of indices present in each expr
        self._exprs_idxs = [
            tuple(filter(expr.find, self.indices)) for
            expr in self.exprs
        ]

        # Group expressions using same set of indices
        self._expr_by_idx = defaultdict(list)
        for idxs, unk, expr in zip(
                self._exprs_idxs, self.unk, self.exprs):
            self._expr_by_idx[idxs].append(sympy.Eq(unk, expr))

        super(ExampleCode, self).__init__(**kwargs)

    def _mk_recursive_loop(self, idxs, body):
        if len(idxs) == 0:
            return body
        else:
            idx = idxs[0]
            return Loop(
                idx.label,
                (idx.lower, idx.upper),
                self._mk_recursive_loop(idxs[1:], body)
            )

    def variables(self):
        expr_groups = []
        for idxs in self._exprs_idxs:
            expr_code = []
            for expr in self._expr_by_idx[idxs]:
                expr_code.append(self.as_arrayified_code(
                    expr.rhs, assign_to=expr.lhs))
            expr_groups.append(self._mk_recursive_loop(
                idxs, expr_code))
        aliases = []

        for number, ind in enumerate(self.indices):
            aliases.extend([
                "const int {} = bnds[{}*2];".format(ind.lower, number),
                "const int {} = bnds[{}*2+1];".format(ind.upper, number)
            ])

        cumul_inplen = 0
        for inp in self.inputs:
            if isinstance(inp, sympy.Indexed):
                aliases.append(
                    "const double * const {} = inpd + {};".format(
                        inp.base.label, cumul_inplen))
                cumul_inplen += inp.indices[0].upper - inp.indices[0].lower
            else:
                aliases.append(
                    "const double {} = inpd[{}];".format(
                        inp, cumul_inplen))
                cumul_inplen += 1

        cumul_outlen = 0
        for out in self.unk:
            if isinstance(out, sympy.Indexed):
                aliases.append(
                    "double * const {} = outd + {};".format(
                        out.base.label, cumul_outlen))
                cumul_outlen += out.indices[0].upper - out.indices[0].lower
            else:
                aliases.append(
                    "double * {} = &outd[{}];".format(
                        out, cumul_outlen))
                cumul_outlen += 1

        return {
            'aliases': aliases,
            'expr_groups': expr_groups
        }

    def __call__(self, inp, bounds=None, inpi=None):
        inp_arr = np.ascontiguousarray(np.concatenate(
            [[x] if isinstance(x, float) else x for x in inp]
        ), dtype=np.float64)
        bounds_arr = np.ascontiguousarray(bounds, dtype=np.int32).flatten()
        if inpi is None:
            inpi_arr = np.empty((0,), dtype=np.int32)
        else:
            inpi_arr = np.ascontiguousarray(inpi, dtype=np.int32)
        assert all([len(u.indices) == 1 for u in self.unk])
        index_subsd = {}
        for idx, pair in zip(self.indices, bounds):
            index_subsd[idx.lower] = pair[0]
            index_subsd[idx.upper] = pair[1]
        noutd = sum([u.indices[0].upper-u.indices[0].lower for u
                     in self.unk]).subs(index_subsd)
        nouti = 0
        outd, outi = self.mod.arbitrary_func(
            bounds_arr, inp_arr, inpi_arr, noutd, nouti)
        output = []
        i = 0
        for u in self.unk:
            n = u.indices[0].upper-u.indices[0].lower
            n = n.subs(index_subsd)
            output.append(outd[i:i+n])
            i += n

        return output


def model1(inps, lims, logger=None):
    """
    x[i] = (a[i]/3-1)**i + c
    y[j] = a[j] - j
    """
    a_arr, c_ = inps
    ilim, jlim = lims

    i_bs = sympy.symbols('i_lb i_ub', integer=True)
    i = sympy.Idx('i', i_bs)

    j_bs = sympy.symbols('j_lb j_ub', integer=True)
    j = sympy.Idx('j', j_bs)

    a = sympy.IndexedBase('a')

    c = sympy.Symbol('c', real=True)

    x = sympy.IndexedBase('x')
    y = sympy.IndexedBase('y')

    eqs = [
        sympy.Eq(x[i], (a[i]/3-1)**i+c),
        sympy.Eq(y[j], a[j]-j),
    ]

    ex_code = ExampleCode(eqs, (a[i], c), (i, j),
                          logger=logger, save_temp=True)
    x_, y_ = ex_code(inps, bounds=(ilim, jlim))
    x_ref = (a_arr/3-1)**np.arange(ilim[0], ilim[1]) + c_
    y_ref = a_arr[jlim[0]:jlim[1]] - np.arange(jlim[0], jlim[1])
    assert np.allclose(x_, x_ref)
    assert np.allclose(y_, y_ref)


def main(logger=None):
    a_arr = np.linspace(0, 10, 11)
    c_ = 3.5
    model1([a_arr, c_], [(0, 11), (0, 7)], logger=logger)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    main(logger=logger)
