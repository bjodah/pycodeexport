// ${_warning_in_the_generated_file_not_to_edit}

<%doc>
   This is a Mako (docs.makotemplates.org/) templated C99-source code
</%doc>

##// Essentially "import pycodeexport.codeexport as ce"
<%namespace name="ce" module="pycodeexport.codeexport"/>

## Mako namespace uses a functools.partial shim, hence .func
<%def name="render_group(group)">
%if isinstance(group, ce.Loop.func):
    ${nested_loop(*group)}
%else:
  %for line in group:
    ${line}
  %endfor
%endif
</%def>


<%def name="nested_loop(ctr, bounds, body, typ='int')">
  for (${typ} ${ctr}=${bounds[0]}; ${ctr}<${bounds[1]}; ++${ctr}){ 
    ${render_group(body)}
  }
</%def>

// func takes arbitrary (<~ 2e9) number of ints and doubles as
// input (inpd/inpi) and populates arbitrary number of doubles
// and ints in outd/outi, returns 0 on successful exit;
int _arbitrary_func(const int * const restrict bnds,
		    const double * const restrict inpd,
		    const int * const restrict inpi,
		    double * const restrict outd,
		    int * const restrict outi)
{
  %for alias in aliases:
    ${alias}
  %endfor
  %for group in expr_groups:
    ${render_group(group)}
  %endfor
  return 0;
}
