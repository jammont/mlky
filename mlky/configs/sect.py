"""
"""
import logging
import os

from glob import glob

import yaml

from .dict import DictSect
from .list import ListSect
from .var  import Var


Logger = logging.getLogger('mlky/sect')


def merge(a, *b):
    """
    Merge dict a into b
    Used to load multiple input files together. Recursively merges multiple dicts if
    provided

    Parameters
    ----------
    a : dict
        Source dictionary
    b : tuple[dict] of len => 1
        Destination dictionaries to merge into
    """
    if len(b) > 1:
        b = (merge(b[0], *b[1:]),)
    [b] = b

    for key, value in a.items():
        if isinstance(value, dict):
            c = b.setdefault(key, {})
            merge(value, c)
        else:
            b[key] = value

    return b


def load_from_str(string):
    """
    """
    # File path
    if os.path.exists(string):
        Logger.debug(f'Loading using yaml.safe_load(file={string})')
        with open(string, 'r') as file:
            data = yaml.safe_load(file)

    # glob wildcard
    elif glob(string):
        data = [load_from_str(file) for file in glob(string)]
        if len(data) > 1:
            data = merge(data[0], *data[1:])
            Logger.debug('Merged files together')

    else:
        try:
            # Raw yaml strings supported only
            data = yaml.safe_load(string)
            Logger.debug('Loaded using yaml.safe_load(string)')
        except:
            raise TypeError(f'Data input is a string but is not a file nor a yaml string: {string}')

    return data


def Switch(key, val, parent, **kwargs):
    """
    Utility function for Sect subclasses to switch input data to the proper object
    container
    """
    obj = Var
    if isinstance(val, (dict, DictSect)):
        obj = DictSect
    elif isinstance(val, (list, ListSect)):
        obj = ListSect

    return obj(key=key, _data=val, parent=parent, **kwargs)


def Sect(*args, **kwargs):
    """
    Create a Sect object depending on the input
    """
    defs = kwargs.get('_defs')
    if isinstance(defs, str):
        defs = load_from_str(kwargs['_defs'])

    if defs:
        kwargs['_defs'] = Sect(defs,
            _labels      = False,
            _coerce      = False,
            _interpolate = False
        )

    if len(args) == 1:
        [data] = args

        if isinstance(data, str):
            data = load_from_str(data)

        if isinstance(data, (dict, DictSect)):
            return DictSect(_data=data, **kwargs)

        elif isinstance(data, (list, ListSect)):
            return ListSect(_data=data, **kwargs)

        else:
            return Var(data, **kwargs)

    elif args:
        return ListSect(_data=args, **kwargs)

    # Default to a DictSect even if no kwargs
    else:
        return DictSect(_data=kwargs, **kwargs)

    # else:
    #     raise AttributeError('*args or **kwargs must be defined, see docs for how to use this function')
