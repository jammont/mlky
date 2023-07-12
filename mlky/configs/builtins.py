"""
"""
import os
import re
import uuid

from . import (
    Null,
    register
)


@register()
def get_env(key, other=''):
    """
    Retrieves an environment variable
    """
    return os.environ.get(key, other)


@register()
def set_env(key, value=''):
    """
    Sets an environment variable
    """
    os.environ[key] = str(value)


@register()
def null(*args, **kwargs):
    return Null()


@register()
def oneof(value, options, regex=False):
    """
    Checks if a given value is one of a list of options
    """
    if regex:
        for opt in options:
            if re.search(opt.replace('//', '/'), value):
                return True
        return f'Invalid option: {value!r}, should regex match one of: {options!r}'
    elif value in options:
        return True
    return f'Invalid option: {value!r}, should be one of: {options!r}'


@register()
def gen_hash(size=None, reset=False):
    """
    Generates a random hash on first call and returns the same for every
    subsequent call until reset is passed
    """
    if reset or not hasattr(gen_hash, 'hash'):
        gen_hash.hash = uuid.uuid4().hex[:size or 6].upper()

    return gen_hash.hash


@register()
def isdir(path):
    return os.path.isdir(path) or f'Directory Not Found: {path}'


@register()
def isfile(path):
    return os.path.isfile(path) or f'File Not Found: {path}'


@register()
def compare(value, lt=None, lte=None, gt=None, gte=None):
    """
    """
    errors = []
    if lt is not None:
        if not value < lt:
            errors.append(f'Value must be less than: {lt!r}')
    if lte is not None:
        if not value <= lte:
            errors.append(f'Value must be less than or equal to: {lte!r}')
    if gt is not None:
        if not value > gt:
            errors.append(f'Value must be greater than: {gt!r}')
    if gte is not None:
        if not value >= gte:
            errors.append(f'Value must be greater than or equal to: {gte!r}')

    return errors or True


@register()
def between(value, a, b, inclusive=False):
    """
    Intuitive syntax for `compare` function

    Parameters
    ----------
    value: any
        The value to compare
    a: any
        The upper bound comparison
    b: any
        The lower bound comparison
    inclusive:
    """
    args = {}
    if inclusive in ['lower', 'both', True]:
        args['gte'] = a
    else:
        args['gt'] = a

    if inclusive in ['upper', 'both', True]:
        args['lte'] = b
    else:
        args['lt'] = b

    if inclusive in ['both', True]:
        args['gte'] = a
        args['lte'] = b
    else:
        if 'upper' in inclusive:
            args['gte'] = a
        else:
            args['ge'] = a
        if 'upper' in inclusive:
            args['gte'] = a
        else:
            args['gte'] = a

    return compare(value, **args)
