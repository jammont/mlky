"""
Tests the mlky Var class
"""
import pickle

import pytest

from mlky import Sect
from mlky.configs.var import Var


@pytest.mark.parametrize("name,key,value,dtype,checks,errors", [
    ('.1', 'one'  , 1, 'None', [{'oneof': [0, 1, 2]}], {}),
    ('.2', 'two'  , 2, 'any' , [{'oneof': [0, 2, 4]}], {}),
    ('.3', 'three', 3, 'int' , [{'oneof': [0, 2, 4]}], {'oneof': 'Invalid option: 3, should be one of: (0, 2, 4)'}),
    ('.4', 'four' , 4, 'str' , [{'oneof': [0, 4, 8]}], {'type': "Wrong type: Expected <'str'> Got <class 'int'>"})
])
def test_Var(name, key, value, dtype, checks, errors):
    """
    Tests initialization and briefly validation
    """
    v = Var(name=name, key=key, value=value, dtype=dtype, checks=checks)
    assert str(v)   == f'<Var({key}={value})>', f'Var str() broken, expected "<Var({key}={value})>" got {str(v)}'
    assert v.name   == name,   f'Bad attribute "name", expected {name} got {v.name}'
    assert v.key    == key,    f'Bad attribute "key", expected {key} got {v.key}'
    assert v.value  == value,  f'Bad attribute "value", expected {value} got {v.value}'
    assert v.dtype  == dtype,  f'Bad attribute "dtype", expected {dtype} got {v.dtype}'
    assert v.checks == checks, f'Bad attribute "checks", expected {checks} got {v.checks}'

    reduced = v.validate().reduce()
    assert reduced == errors, f'Bad errors, expected {errors} got {reduced}'

    # return True


def test_pickle():
    """
    Tests serializability
    """
    sect = Sect({'a': 1, 'b': {'c': ['z', 'y']}})

    data = pickle.dumps(sect)
    load = pickle.loads(data)

    assert sect == load, 'Loaded pickle data does not match original'

    # return True
