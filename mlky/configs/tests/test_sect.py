"""
Tests the mlky Sect and NullDict classes
"""
import pickle

import pytest

from mlky import (
    Null,
    DictSect,
    ListSect,
    Sect,
    Var
)


Cases = [
    {'a': 1, 'b': {'c': ['z', 'y']}},
    {'a': [0, 1], 'b': [{'z': 1}, {'y': 2}]}
]


def test_isinstance():
    """
    Tests isinstance
    """
    sect = Sect({'a': 1, 'b': {'c': 2}, 'd': [3, 4]})
    assert isinstance(sect  , DictSect), f'Expected DictSect, got {type(sect)}'
    assert isinstance(sect.a, int     ), f'Expected int, got {type(sect.a)}'
    assert isinstance(sect.b, DictSect), f'Expected DictSect, got {type(sect.b)}'
    assert isinstance(sect.d, ListSect), f'Expected ListSect, got {type(sect.d)}'


@pytest.mark.parametrize('data', Cases)
def test_recursive(data):
    """
    Tests that Sects are recursive with themselves
    """
    sect = Sect(data)
    assert sect == Sect(sect), 'sect != Sect(sect)'


@pytest.mark.parametrize('data', Cases)
def test_pickle(data):
    """
    Tests serializability
    """
    sect = Sect(data)

    data = pickle.dumps(sect)
    load = pickle.loads(data)

    assert sect == load, 'Loaded pickle data does not match original'


@pytest.mark.parametrize('data', Cases)
def test_deepcopy(data):
    """
    Tests deep copy functionality
    """
    sect = Sect(data)
    copy = sect.deepCopy()
    assert copy == sect, 'The copy did not match the original'


@pytest.mark.parametrize('data,solution', [
    ([{'a': 1}, {'b': 2}, {'a': -1}, {'c': 3}], {'a': -1, 'b': 2, 'c': 3}),
    ([{'a': 1}, {'b': [2]}, {'a': -1}, {'b': 2}], {'a': -1, 'b': 2}),
    ([{'a': {'x': 1, 'y': 2}}, {'a': {'x': -1, 'z': 3}}], {'a': {'x': -1, 'y': 2, 'z': 3}}),
])
def test_patching(data, solution):
    base = Sect()
    for d in data:
        base |= Sect(d)

    assert base == solution, f'Patching failed to match solution, expected {solution}, got {base.toDict()}'


def test_operators():
    """
    """
    base = Sect()

    # assert base < {'a': 1} == {'a': 1}
    assert base | {'a': 1} == {'a': 1}
    assert base | {'a': 1} | {'b': 2} == {'a': 1, 'b': 2}


def test_get():
    """
    Tests Sect.get() for a few simple cases
    """
    data = {'a': 1, 'b': {'c': 3}, 'd': ['e', 'f']}
    defs = {'.a': {'dtype': int, 'default': -1}, '.g': {'dtype': int, 'default': 7}}
    sect = Sect(data, _defs=defs)

    # .a is a
    var = sect.get('a', var=True)
    assert sect.get('a') == 1, '.get did not return the expected value'
    assert isinstance(var, Var), '.get(var=True) did not return a Var'
    assert var._defs.default == -1, 'defs default did not set on existing key properly'

    # .g is a defs created key
    var = sect.get('g', var=True)
    assert sect.get('g') == 7, 'Should return default if key was from defs'
    # assert sect.get('g', default=False) is None, 'Should return None if key was from defs and default=False'

    assert isinstance(var, Var), '.get(var=True) did not return a Var'
    assert var.value is Null, 'defs key .value should be Null'
    assert var._defs.default == 7, 'defs key .default was wrong'
