"""
"""
import glob
import logging
import os

from pathlib import Path

import yaml

from .dict import DictSect
from .list import ListSect
from .var  import Var

# Allows custom types to override the defaults for the functions
types = {
    'dict': DictSect,
    'list': ListSect,
    'var': Var
}


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
    elif glob.has_magic(string):
        data = [load_from_str(file) for file in glob.glob(string)]
        if len(data) > 1:
            data = merge(data[0], *data[1:])
            Logger.debug('Merged files together')
        elif not data:
            Logger.error(f'No files were collected using the provided glob string: {string}')

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
    obj = types['var']
    if isinstance(val, (dict, types['dict'])):
        obj = types['dict']
    elif isinstance(val, (list, types['list'])):
        obj = types['list']

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

        if isinstance(data, (str, Path)):
            data = load_from_str(str(data))

        if isinstance(data, (dict, types['dict'])):
            return types['dict'](_data=data, **kwargs)

        elif isinstance(data, (list, types['list'])):
            return types['list'](_data=data, **kwargs)

        else:
            return types['var'](data, **kwargs)

    elif args:
        return types['list'](_data=args, **kwargs)

    # Default to a DictSect even if no kwargs
    else:
        return types['dict'](_data=kwargs, **kwargs)

    # else:
    #     raise AttributeError('*args or **kwargs must be defined, see docs for how to use this function')
