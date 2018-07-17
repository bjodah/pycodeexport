

def line_cont_after_delim(ctx, s, line_len=40, delim=(',',),
                          line_cont_token='&'):
    """
    Insert newline (with preceeding `line_cont_token`) afer
    passing over a delimiter after traversing at least `line_len`
    number of characters

    Mako convenience function. E.g. fortran does not
    accpet lines of arbitrary length.
    """
    last = -1
    s = str(s)
    for i, t in enumerate(s):
        if t in delim:
            if i > line_len:
                if last == -1:
                    raise ValueError(
                        'No delimiter until already past line_len')
                i = last
                return s[:i+1] + line_cont_token + '\n ' + \
                    line_cont_after_delim(
                        ctx, s[i+1:], line_len, delim)
            last = i
    return s
