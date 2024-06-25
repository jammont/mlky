"""
Tests the mlky Var class
"""
import pickle

import pytest

from mlky import (
    Sect,
    Var
)


def test_flag_coerce():
    """
    """
    s = Sect({'a': 1})
    v = s.get('a', var=True)
    assert isinstance(v, Var)
    assert v._coerce == True

    s.a = '2'
    assert s.a == 2

    s = Sect({'a': 1}, _coerce=False)
    v = s.get('a', var=True)
    assert isinstance(v, Var)
    assert v._coerce == False

    s.a = '2'
    assert s.a == '2'


def test_subtypes():
    """
    """
    defs = """\
    .multi:
        sdesc: This is a multi-typed variable
        default: 1
        subtypes:
            - dtype: int
              default: 1
              checks:
                - compare:
                    gt: 0
            - dtype: str
              default: '/some/file'
              checks:
                - isfile
    """
    s = Sect(_defs=defs)

    s.multi = 'abc'
    assert s.validateObj(asbool=False, report=False) == {'.multi': {'isfile': 'File Not Found: abc'}}, 'Failed to switch subtype to str'

    s.multi = -1
    assert s.validateObj(asbool=False, report=False) == {'.multi': {'compare': ['Value must be greater than: 0']}}, 'Failed to switch subtype to int'


def test_nullsEqMissing():
    """
    """
    defs = """\
    .multi:
        subtypes:
            - dtype: int
              default: 1
            - dtype: str
              default: 'a'
    """
    data = """\
    multi: \\
    """

    s = Sect(data, _defs=defs, _nullsEqMissing=True)
    v = s.get('multi', var=True)

    assert s.multi == 'a', 'Failed to switch subtype and retrieve dtype'

    s.multi = 3
    assert s.multi == 3, 'Failed to switch subtype'
