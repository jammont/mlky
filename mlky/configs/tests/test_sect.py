"""
Tests the mlky Sect and NullDict classes
"""
import pickle

import pytest

from mlky import (
    Null,
    Sect
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

    # return True


@pytest.mark.parametrize('data', Cases)
def test_recursive(data):
    """
    Tests that Sects are recursive with themselves
    """
    sect = Sect(data)
    assert sect == Sect(sect), 'sect != Sect(sect)'

    # return True


@pytest.mark.parametrize('data', Cases)
def test_pickle(data):
    """
    Tests serializability
    """
    sect = Sect(data)

    data = pickle.dumps(sect)
    load = pickle.loads(data)

    assert sect == load, 'Loaded pickle data does not match original'

    # return True


@pytest.mark.parametrize('data', Cases)
def test_deepcopy(data):
    """
    Tests deep copy functionality
    """
    sect = Sect(data)
    copy = sect.deepCopy()
    assert copy == sect, 'The copy did not match the original'

    # return True


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

    # return True


def test_operators():
    """
    """
    base = Sect()

    assert base < {'a': 1} == {'a': 1}
    assert base | {'a': 1} == {'a': 1}
    assert base | {'a': 1} | {'b': 2} == {'a': 1, 'b': 2}

    # return True
