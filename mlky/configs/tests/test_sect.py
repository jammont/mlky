"""
Tests the mlky Sect and NullDict classes
"""
import pickle

import pytest

from mlky import (
    Null,
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
    sect = Sect({'a': {'x': 1, 'y': 2}, 'b': 3, 'c': [-1, -2]})
    assert isinstance(sect, Sect), 'Instance is not isinstance of Sect'
    assert isinstance(sect.a, Sect), 'Instance is not isinstance of Sect'
    assert isinstance(sect.c, Sect), 'Instance is not isinstance of Sect'


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
def test_patching(data, solution, debug=False):
    base = Sect(debug=debug)
    for d in data:
        base |= Sect(d, debug=debug)

    assert base == solution, f'Patching failed to match solution, expected {solution}, got {base.toDict()}'


def test_operators():
    """
    """
    base = Sect()

    assert base < {'a': 1} == {'a': 1}
    assert base | {'a': 1} == {'a': 1}
    assert base | {'a': 1} | {'b': 2} == {'a': 1, 'b': 2}


def test_get():
    """
    Tests Sect.get() for a few simple cases
    """
    data = {'a': 1, 'b': {'c': 3}, 'd': ['e', 'f']}
    defs = {'.a': {'default': -1}, '.g': {'default': 7}}
    sect = Sect(data=data, defs=defs)

    # .a is a
    var = sect.get('a', var=True)
    assert sect.get('a') == 1, '.get did not return the expected value'
    assert isinstance(var, Var), '.get(var=True) did not return a Var'
    assert var.default == -1, 'defs default did not set on existing key properly'

    # .g is a defs created key
    var = sect.get('g', var=True)
    assert sect.get('g') == 7, 'Should return default if key was from defs'
    assert sect.get('g', default=False) is None, 'Should return None if key was from defs and default=False'

    assert isinstance(var, Var), '.get(var=True) did not return a Var'
    assert var.value is Null, 'defs key .value should be Null'
    assert var.default == 7, 'defs key .default was wrong'


def test_opts():
    """
    Test combinations of Sect._opts
    """
    Sect._opts.convertListTypes = False
    Sect._opts.convertItems     = True

    S = Sect({'a': 1, 'b': {'c': 2}, 'd': [3, {'f': {'g': 4, 'h': [5, 'i']}}]})

    assert S.a == 1
    assert S.b == {'c': 2}

    assert isinstance(S.d, list)
    assert S.d[0] == 3

    assert isinstance(S.d[1], Sect)
    assert isinstance(S.d[1].f, Sect)
    assert S.d[1].f.g == 4

    assert isinstance(S.d[1].f.h, list)
    assert S.d[1].f.h[0] == 5
    assert S.d[1].f.h[1] == 'i'

    Sect._opts.convertListTypes = False
    Sect._opts.convertItems     = False

    S = Sect({'a': [[0, 1], [2, 3]]})
    assert S.a == [[0, 1], [2, 3]]
