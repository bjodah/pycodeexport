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
    cdef cnp.ndarray[cnp.int32_t, ndim=1] arr_bounds = np.asarray(bounds, dtype=np.int32)
    cdef cnp.ndarray[cnp.float64_t, ndim=1] arr_inpd = np.asarray(inpd, dtype=np.float64)
    cdef cnp.ndarray[cnp.int32_t, ndim=1] arr_inpi = np.asarray(inpi, dtype=np.int32)
    cdef cnp.ndarray[cnp.float64_t, ndim=1] arr_outd = np.empty(noutd, dtype=np.float64)
    cdef cnp.ndarray[cnp.int32_t, ndim=1] arr_outi = np.empty(nouti, dtype=np.int32)
    cdef int status = _arbitrary_func(
        <int *>arr_bounds.data,
        <double *>arr_inpd.data,
        <int *>arr_inpi.data,
        <double *>arr_outd.data,
        <int *>arr_outi.data
    )
    if status != 0: raise RuntimeError(
            "_arbitrary_func unsuccessful (status={})".format(status))
    return arr_outd, arr_outi
