# -*- coding: utf-8 -*-
# ${_warning_in_the_generated_file_not_to_edit}
import numpy as np
cimport numpy as cnp

%for (opname, opfmt, vec_opfmt), (ctype, nptype, vectype, vecsize) in combos:
cdef extern void c_elem${opname}_${ctype}(
    const ${idxtype} N, const ${ctype}* a, const ${ctype}* b, ${ctype}* z)

%if vec_opfmt != None:
cdef extern void c_vec${opname}_${ctype}(
    const ${idxtype} N, const ${ctype}* a, const ${ctype}* b, ${ctype}* z)
%endif
%endfor

%for opname, opfmt, vec_opfmt in ops:
def elem${opname}(a, b):
    if not isinstance(a, np.ndarray):
        raise TypeError('Numpy arrays only supported.')
    %for ctype, nptype, vectype, vecsize in types:
    elif a.dtype == np.${nptype}:
        return _elem${opname}_${ctype}(a,b)
    %endfor
    raise RuntimeError('Unsupported dtype')

%if vec_opfmt != None:
def vec${opname}(a, b):
    if not isinstance(a, np.ndarray):
        raise TypeError('Numpy arrays only supported.')
    %for ctype, nptype, vectype, vecsize in types:
    elif a.dtype == np.${nptype}:
        return _vec${opname}_${ctype}(a,b)
    %endfor
    raise RuntimeError('Unsupported dtype')
%endif
%endfor

%for (opname, opfmt, vec_opfmt), (ctype, nptype, vectype, vecsize) in combos:
cdef cnp.ndarray[cnp.${nptype}_t, ndim=1] _elem${opname}_${ctype}(${ctype} [:] a,
                               ${ctype} [:] b):
    cdef cnp.ndarray[cnp.${nptype}_t, ndim=1] c = np.empty_like(
        a, dtype=np.${nptype})
    c_elem${opname}_${ctype}(a.shape[0], &a[0], &b[0], &c[0])
    return c

%if vec_opfmt != None:
cdef cnp.ndarray[cnp.${nptype}_t, ndim=1] _vec${opname}_${ctype}(${ctype} [:] a,
                               ${ctype} [:] b):
    cdef cnp.ndarray[cnp.${nptype}_t, ndim=1] c = np.empty_like(
        a, dtype=np.${nptype})
    c_vec${opname}_${ctype}(a.shape[0], &a[0], &b[0], &c[0])
    return c
%endif
%endfor
