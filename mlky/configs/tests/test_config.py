"""
Tests the mlky Config class
"""
import pytest

from mlky import (
    Config,
    Null
)


def test_init():
    """
    Tests various use cases of initializing Config instances
    """
    data = {'a': 1, 'b': 2}
    cfg1 = Config(data)
    assert cfg1 == data, 'Config did not match input data'

    cfg2 = Config()
    assert cfg2 == data, 'Config() did not match previously initialized Config'

    data = {'x': 1, 'y': 2}
    cfg3 = Config(data)
    assert cfg1 == data, 'Reinitialized config did not match new input'
    assert cfg2 == data, 'Reinitialized config did not match new input'
    assert cfg3 == data, 'Reinitialized config did not match new input'

    altL = {'l': 1}
    cfgL = Config(altL, local=True)
    assert cfgL == altL, 'Local initialization does not match input'
    assert cfg1 == data, 'Local initialization broke the global instance'
    assert cfg2 == data, 'Local initialization broke the global instance'
    assert cfg3 == data, 'Local initialization broke the global instance'

    data = ['j', 'k', 'l']
    cfg4 = Config(data)
    assert cfgL == altL, 'Local initialization did not persist global instance reinitialization'
    assert cfg1 == data, 'Reinitialized config did not match new input'
    assert cfg2 == data, 'Reinitialized config did not match new input'
    assert cfg3 == data, 'Reinitialized config did not match new input'
    assert cfg4 == data, 'Reinitialized config did not match new input'


@pytest.mark.parametrize('data,keys', [
    ({'a': {'f': {'m': {'r': {'s': 7}}}, 'y': 2}, 'b': {'x': -1}, 'c': {'z': 3}}, ['a', 'b', 'c'])
])
def test_yamlDifferences(data, keys):
    """
    Tests changes in a config and copies, and dumping and loading yamls
    """
    return # TODO: Temporarily disabled while dumpYaml is under construction

    # First initialization
    conf = Config(data, keys)

    # Create a copy
    copy = conf.deepCopy()
    assert copy == conf, 'Copy did not match conf'

    # Tweak it to ensure they differ
    copy.diff = 1
    assert copy != conf, 'Copy should not match conf after changing'

    # Make sure the dumps differ too
    dump = copy.dumpYaml()
    assert dump != conf.dumpYaml(), 'YAML dumps should not match'

    # Change the copy further to compare with loading
    copy.load = False

    # Recreate from dump as a local instance
    load = Config(dump, ['generated'], local=True)
    assert load != copy, '`load` should not match the `copy` as it was changed after dumping'
    assert load != conf, '`load` should not match the `conf`'

    # Delete the differences and ensure equality
    del copy.load
    assert load == copy, '`load` should now match `copy` after deleting the conflicting key'
    assert load != conf, '`load` should not match `conf` yet'

    del load.diff
    assert load != copy, '`load` should not match `copy` anymore'
    assert load == conf, '`load` should now match `conf` after deleting the conflicting key'


def test_replace():
    """
    Tests the replacement logic of Vars through the Config
    """
    C = Config({'a': 1, 'b': '${.a}'})
    assert C.a == 1
    assert C.b == '1'

    C = Config({'a': '${.b}', 'b': 2})
    assert C.a == '2'
    assert C.b == 2


YAML = """\
a: \\
b: //
d: -1
e: -1
"""

DEFS = """\
.a:
    dtype: str
.b:
    dtype: str
.c:
    dtype: str
    default: C
.d:
    dtype: int
.e:
    dtype: float
.f:
    dtype: str
"""

def test_replace():
    """
    Test function to validate the behavior of the 'replace' function.

    This function creates a 'Config' instance using the provided YAML data and definitions.
    It then asserts various attributes of the 'Config' instance to ensure proper replacement.

    Asserts
    -------
    - 'a' should be Null
    - 'b' should be '//'
    - 'c' should be 'C' (default value)
    - 'd' should be -1
    - 'e' should be -1. (float type)
    """
    Config(data=YAML, defs=DEFS)

    assert Config.a is Null
    assert Config.b == '//'
    assert Config.c == 'C'
    assert Config.d == -1
    assert Config.e == -1.
