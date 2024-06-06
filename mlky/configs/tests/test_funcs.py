"""
Tests mlky builtin functions
"""
import pytest

from mlky import (
    funcs,
    Null
)


# @pytest.mark.parametrize("value,dtype,valid", [
#     # Single types, must be exact
#     ('1', str, True),
#     (1, int, True),
#     (1., float, True),
#     ([1], list, True),
#     ({1}, set, True),
#     ({1: 0}, dict, True),
#     # Multi-type checks, must be one of
#     ('1', [int, str], True),
#     (1, [int, str], True),
#     (1, [int, float], True),
#     (1., [int, float], True),
#     ('1', [int, float, str], True),
#     (1, [int, float, str], True),
#     (1., [int, float, str], True),
#     # Any type checks, value shouldn't matter
#     (1,  'any', True), ('1',  'any', True), (1.,  'any', True), ([1],  'any', True), ({1},  'any', True),
#     (1,   None, True), ('1',   None, True), (1.,   None, True), ([1],   None, True), ({1},   None, True),
#     (1,   Null, True), ('1',   Null, True), (1.,   Null, True), ([1],   Null, True), ({1},   Null, True),
#     (1, 'None', True), ('1', 'None', True), (1., 'None', True), ([1], 'None', True), ({1}, 'None', True),
#     (1, 'Null', True), ('1', 'Null', True), (1., 'Null', True), ([1], 'Null', True), ({1}, 'Null', True),
#     # Bad single type checks
#     (1, str, False),
#     ('1', int, False),
#     (1, float, False),
#     (1, list, False),
#     (1, set, False),
#     (1, dict, False),
#     # Bad multi-type checks
#     (1., [int, str], False),
#     ({1}, [int, str], False),
#     ('1', [int, float], False),
#     ({1}, [int, float], False),
#     ({1}, [int, float, str], False),
#     ([1], [int, float, str], False),
# ])
# def test_dtypes(value, dtype, valid):
#     got = funcs.getRegister('check_dtype')(value, dtype)
#     if valid:
#         assert got is True, f'Expected True check for {value=}, {dtype=}, got: {got}'
#     else:
#         if isinstance(dtype, list):
#             assert "is not one of" in got, f"Expected 'is not one of' error for {value=}, {dtype=}, got: {got}"
#         else:
#             assert "Wrong type" in got, f"Expected 'Wrong type' error for {value=}, {dtype=}, got: {got}"
