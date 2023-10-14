"""
Houses all of the built-in register functions of mlky. These are generalized
functions that may be applicable to a wide variety of use cases.
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

    Parameters
    ----------
    key: str
        Key name for the environment variable to retrieve
    other: any, defaults=''
        Return this value if the key doesn't exist in the environment

    Returns
    -------
    str, any
        If the key exists the return will be a str, otherwise return the `other`
        parameter
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
    """
    Returns a Null value

    Returns
    -------
    mlky.Null
        A mlky Null object, please see Null documentation for more information
    """
    return Null()


@register('os.cpu_count')
def cpu_count(*args):
    """
    Wrapper to access the os.cpu_count() function

    Returns
    -------
    int
        The return of os.cpu_count()
    """
    return os.cpu_count()


@register()
def oneof(value, *options, regex=False):
    """
    Checks if a given value is one of a list of options

    Parameters
    ----------
    value: any
        Some value to check if it is one of the `options` provided
    options: list
        List of objects to check if `value` is in
    regex: bool, defaults=False
        Informs that the options of the list are regex strings to compare to.
        The `value` is oneof `options` if `value` regex matches to any option.

    Returns
    -------
    True, str
        Returns True if `value` is oneof `options`, otherwise return an error
        message as a string
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
def gen_hash(size=6, reset=False):
    """
    Generates a random hash on first call and returns the same for every
    subsequent call until reset is passed

    Parameters
    ----------
    size: int, defaults=6
        The length of the hash string to generate
    reset: bool, defaults=False
        Whether to reset the currently generated hash

    Returns
    -------
    str
        Randomly generated hash string
    """
    if reset or not hasattr(gen_hash, 'hash'):
        gen_hash.hash = uuid.uuid4().hex[:size].upper()

    return gen_hash.hash


@register()
def isdir(path):
    """
    Simply performs os.path.isdir()

    Parameters
    ----------
    path: str
        Directory path to check existence

    Returns
    -------
    bool or str
        Returns True if the path exists, otherwise returns an error string
    """
    return os.path.isdir(path) or f'Directory Not Found: {path}'


@register()
def isfile(path):
    """
    Simply performs os.path.isfile()

    Parameters
    ----------
    path: str
        File path to check existence

    Returns
    -------
    bool or str
        Returns True if the path exists, otherwise returns an error string
    """
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
    inclusive: bool or str, defaults=False
        Boundary inclusivity:
        - False   = Both bounds are exclusive
        - 'lower' = The lower bound is inclusive, upper is not
        - 'upper' = The upper bound is inclusive, lower is not
        - 'both'  = Both bounds are inclusive
        - True    = Both bounds are inclusive

    Returns
    -------
    list or True
        Returns compare(value) with the correct bounds. If `value` is
        within specified bounds, return True, else return a list of strings
        which are the error message(s).
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

    return compare(value, **args)
