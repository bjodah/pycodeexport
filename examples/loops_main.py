#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict

import numpy as np
import sympy

from pycompilation.codeexport import C_Code, Loop

def get_statements(eq, taken=None):
    """
    Returns a list of Eq objects were lhs is variable to make
    assignment to and rhs is expr to be evaluated.

    Transforms Sum() and Product() objects into Loop instances
    """

    def argify(a):
        if arg.is_Symbol:
            return a
        else:
            if isinstance(a, sympy.Sum):
                # s = Dummy()
                expr, loopv = a.args[0], a.args[1]
                sub_stmnts = get_statements(expr)
                return Loop(sub_stmnts, loopv)
            elif isinstance(a, sympy.Product):
                raise NotImplementedError
            else:
                raise NotImplementedError

    return map(argify, eq)


def get_idxs(exprs):
    """
    Finds sympy.tensor.indexed.Idx instances and returns them.
    """
    idxs = set()
    for expr in (exprs):
        for i in expr.find(sympy.Idx):
            idxs.add(i)
    return sorted(idxs, cmp=lambda x,y: str(x)<str(y))



class ExampleCode(C_Code):
    """
    Render _arbitrary_func to do loops
    """
    CompilerRunner = None # auto-detect
    templates = ['loops_template.c']
    source_files = ['loops.c',
                    'loops_wrapper.pyx']
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
            indices, cmp=lambda x,y: str(x)<str(y)) # sanity check

        # list of lists of indices present in each expr
        self._exprs_idxs = [
            tuple(filter(expr.find, self.indices)) for\
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
                self.indices.index(idx),
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
        cumul_inplen = 0
        for inp in self.inputs:
            if isinstance(inp, sympy.Indexed):
                aliases.append(
                    "const double * const {} = inpd + {};".format(
                        inp.indices[0].label, cumul_inplen))
                cumul_inplen += inp.indices[0].upper-\
                                inp.indices[0].lower
            else:
                aliases.append(
                    "const double {} = inpd[{}];".format(
                        inp, cumul_inplen))
                cumul_inplen += 1

        cumul_outlen = 0
        for out in self.unk:
            if isinstance(out, sympy.Indexed):
                aliases.append(
                    "const double * const {} = outd + {};".format(
                        out.indices[0].label, cumul_outlen))
                cumul_outlen += out.indices[0].upper-\
                                out.indices[0].lower
            else:
                aliases.append(
                    "const double {} = outd[{}];".format(
                        out, cumul_outlen))
                cumul_outlen += 1

        print(aliases)
        return {
            'aliases': aliases,
            'expr_groups': expr_groups
        }


    def __call__(self, inp, bounds=None, inpi=None):
        inpd = np.ascontiguousarray(np.concatenate(
            [[x] if isinstance(x, float) else x for x in inp]))
        assert all([len(u.indices) == 1 for u in self.unk])
        noutd = sum([u.indices[0].upper-u.indices[0].lower for u\
                     in self.unk])
        nouti = 0
        outd, outi = self.mod.arbitrary_func(
            bounds, inpd, inpi, noutd, nouti)
        output = []
        i = 0
        for u in self.unk:
            n = u.indices[0].upper-u.indices[0].lower
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


    # a_size >= i_ub - i_lb
    a_size = sympy.Symbol('a_size', integer=True)
    a = sympy.IndexedBase('a', shape=(a_size,))

    c = sympy.Symbol('c', real=True)

    x = sympy.IndexedBase('x', shape=(a_size,))
    y = sympy.IndexedBase('y', shape=(a_size,))

    eqs = [
        sympy.Eq(x[i], (a[i]/3-1)**i+c),
        sympy.Eq(y[j], a[j]-j),
    ]

    ex_code = ExampleCode(eqs, (a[i], c), (i, j),
                          logger=logger, save_temp=True)
    x_, y_ = ex_code(inps, bounds=(i_bs, j_bs))
    assert np.allclose(
        x_,
        (a_arr/3-1)**np.arange(ilim[0], ilim[1]+1) + c_)
    assert np.allclose(
        y_,
        a_arr - np.arange(jlim[0],jlim[1]+1))


def model2():
    """
    y[j] = Sum(a[i], i, j-2, j+2)
    """
    pass

def main(logger=None):
    a_arr = np.linspace(0,10,11)
    c_ = 3.5
    model1([a_arr, c_], [(0,11), (0,7)], logger=logger)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    main(logger=logger)
