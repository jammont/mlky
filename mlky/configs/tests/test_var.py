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
