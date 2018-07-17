from pycodeexport.codeexport import syntaxify_getitem


def test_syntaxify_getitem():
    s1 = syntaxify_getitem('C', 'y_i = x_i+i;', 'y', 'yout',
                           offset='CONST', match_regex=r'_(\w)')
    assert s1 == 'yout[i+CONST] = x_i+i;'

    s2 = syntaxify_getitem('F', 'y7 = x7+i;', 'y', 'yout',
                           offset=-3, dim=-1)
    assert s2 == 'yout(7-3,:) = x7+i;'

    s3 = syntaxify_getitem('C', 'dummy12 = alpha + beta;', 'dummy', 'output')
    assert s3 == 'output[12] = alpha + beta;'
