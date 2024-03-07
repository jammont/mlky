"""
Tests mlky magics
"""
import re

import pytest

from mlky.configs import magic_regex

@pytest.mark.parametrize("string,expected", [
    ("${.}", True),
    ("${.n}", True),
    ("${.\}", True),
    ("${.0}", True),
    ("${..}", True),
    ("${$}", True),
    ("${$n}", True),
    ("${$\}", True),
    ("${$0}", True),
    ("${$.}", True),
    ("${!}", True),
    ("${!n}", True),
    ("${!\}", True),
    ("${!0}", True),
    ("${!.}", True),
    ("", False),
    ("$", False),
    ("${", False),
    ("${}", False),
    ("${?}", False),
    ("${@}", False),
    ("${n}", False),
    ("${\}", False),
    ("${0}", False),
    (".n", False),
    ("$n", False),
    ("!n", False),
])
def test_magic_regex(string, expected):
    """
    Ensures the regex is working in expected ways
    """
    assert bool(re.match(magic_regex, string)) == expected
