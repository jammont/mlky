"""
"""
import yaml

from milkylib.configs.v3 import (
    Config,
    Section,
    Null
)

def test_local(input={'a': 1, 'b': 2}):
    """
    Tests:
    - A local instance's data should not be the class instance's data
    - Multiple instances of the class should share the same data
    """
    config = Config(input)
    local  = Config(local=True)

    assert local._sect is not config._sect, 'A local instance shares the same _sect object with the class instance'

    new = Config()

    assert new._sect is config._sect, 'A new class instance does not share the same _sect object with another class instance'

    return True

def test_inheritance(input=None):
    """
    """
    input = {
        'a': {
            'z': 0
        },
        'b': {
            'z': 1,
            'y': 1
        },
        'c': {
            'z': 2,
            'x': 2
        }
    }

    a = Config(input, local=True, inherit=['a', 'b']     )
    b = Config(input, local=True, inherit=['a', 'b', 'c'])

    assert a.z == 1, 'Inheritance failed to apply a<-b'
    assert a.y == 1, 'Inheritance failed to apply a<-b'

    assert b.z == 2, 'Inheritance failed to apply a<-b<-c'
    assert b.y == 1, 'Inheritance failed to apply a<-b<-c'
    assert b.x == 2, 'Inheritance failed to apply a<-b<-c'

    return True

def test_validate(dir='/Users/jamesmo/projects/milkylib/milkylib/configs/tests/yamls/'):
    rules = yaml.load(open(f'{dir}/rules.yml', 'r'), Loader=yaml.FullLoader)

    good = yaml.load(open(f'{dir}/good.yml', 'r'), Loader=yaml.FullLoader)

    assert Config.validate(rules=rules, data=good, _raise=False) == {1: [], 2: [], 3: []}, 'The good case failed with errors'

    bad = yaml.load(open(f'{dir}/bad.yml', 'r'), Loader=yaml.FullLoader)

    assert Config.validate(rules=rules, data=bad, _raise=False) == {
        1: [
            '.sect1.attr1',
            '.sect3'
        ],
        2: [],
        3: [
            ('.sect1.attr2', 'int', 'str', 'abc'),
            ('.sect1.sub1.attr3', 'bool', 'float', 1.0),
            ('.sect1.sub1.attr4', 'list', 'str', '(a, b)'),
            ('.sect2.attr5', 'float', 'bool', True),
            ('.sect2.attr6', 'str', 'list', ['a', 'b', 'c']),
            ('.sect4[0].attr8', 'str', 'int', 0),
            ('.sect4[1].attr8', 'str', 'int', 1),
            ('.sect4[0].attr9', 'int', 'str', 'jkl'),
            ('.sect4[1].attr9', 'int', 'str', 'mno'),
            ('.sect4[1].attr10', 'bool', 'int', -1)
        ]
    }, 'The bad case did not return the expected errors'

    return True
