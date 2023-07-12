import pickle

from mlky import Config

def init(file, sections=[]):
    defs = Config(file)._data['definitions']
    return Config(file, sections, defs=defs, _raise=False)

def test_pickle(sections=[]):
    """
    """
    sect = init('mlky/configs/tests/yamls/test1.yml', sections)._sect

    data = pickle.dumps(sect)
    load = pickle.loads(data)

    for key in sect.types:
        assert sect.types[key] == load.types[key]

    return True

test_pickle('lawful-good')
