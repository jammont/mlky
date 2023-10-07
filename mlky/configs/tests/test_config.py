"""
Tests the mlky Config class
"""
import pytest

from mlky import Config


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
    answ = {0: 'j', 1: 'k', 2: 'l'} # Sects are always dicts, converts lists to dicts
    cfg4 = Config(data)
    assert cfgL == altL, 'Local initialization did not persist global instance reinitialization'
    assert cfg1 == answ, 'Reinitialized config did not match new input'
    assert cfg2 == answ, 'Reinitialized config did not match new input'
    assert cfg3 == answ, 'Reinitialized config did not match new input'
    assert cfg4 == answ, 'Reinitialized config did not match new input'

    # return True


@pytest.mark.parametrize('data,keys', [
    ({'a': {'f': {'m': {'r': {'s': 7}}}, 'y': 2}, 'b': {'x': -1}, 'c': {'z': 3}}, ['a', 'b', 'c'])
])
def test_yamlDifferences(data, keys):
    """
    Tests changes in a config and copies, and dumping and loading yamls
    """
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

    # return True
