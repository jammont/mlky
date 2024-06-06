"""
Tests mlky magics
"""
import re

import pytest

from mlky import MAGIC

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
    ("${}", True),
    ("${?}", True),
    ("${@}", True),
    ("${n}", True),
    ("${\}", True),
    ("${0}", True),
    (".n", False),
    ("$n", False),
    ("!n", False),
    # Test strings that have magics but don't start with it
    (". ${.}", True),
    (". ${.n}", True),
    (". ${.\}", True),
    (". ${.0}", True),
    (". ${..}", True),
    (". ${$}", True),
    (". ${$n}", True),
    (". ${$\}", True),
    (". ${$0}", True),
    (". ${$.}", True),
    (". ${!}", True),
    (". ${!n}", True),
    (". ${!\}", True),
    (". ${!0}", True),
    (". ${!.}", True),
])
def test_magic_regex(string, expected):
    """
    Ensures the regex is working in expected ways
    """
    assert bool(re.findall(MAGIC, string)) == expected
