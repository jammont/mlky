"""
Tests the mlky Config class
"""
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
