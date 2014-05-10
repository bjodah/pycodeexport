# -*- coding: utf-8 -*-
cimport numpy as cnp
import numpy as np

cdef extern int _arbitrary_func(
    const int * const bounds,
    const double * const inpd,
    const int * const inpi,
    double * const outd,
    int * const outi)

def arbitrary_func(int [::1] bounds,
                   double [::1] inpd,
                   int [::1] inpi,
                   int noutd, int nouti):
    """ Thin Cython shim for passing array data to _arbitrary_func """
    cdef cnp.ndarray[cnp.float64_t, ndim=1] outd = np.empty(
        noutd, dtype=np.float64)
    cdef cnp.ndarray[cnp.int32_t, ndim=1] outi = np.empty(
        nouti, dtype=np.int32)
    cdef int status = _arbitrary_func(
        &bounds[0], &inpd[0], &inpi[0], &outd[0], <int *>&outi[0])
    if status != 0: raise RuntimeError(
            "_arbitrary_func unsuccessful (status={})".format(status))
    return outd, outi
