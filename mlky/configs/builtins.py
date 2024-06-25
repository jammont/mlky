"""
Houses all of the built-in register functions of mlky. These are generalized
functions that may be applicable to a wide variety of use cases.
"""
import os
import re
import uuid

from .funcs import register
from .null  import Null


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
    str | any
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


@register(name='os.cpu_count')
def cpu_count(*args):
    """
    Wrapper to access the os.cpu_count() function

    Returns
    -------
    int
        The return of os.cpu_count()
    """
    return os.cpu_count()


@register(name='nan')
def nan(*args):
    """
    Replaces ${!nan} with float('nan')

    Returns
    -------
    float
        NaN
    """
    return float('NaN')


@register()
def oneof(var, *opts, options=[], regex=False):
    """
    Checks if a given value is one of a list of options

    Parameters
    ----------
    var: mlky.Var
        Checks the var.value against `options`
    *opts: list
        Captures options passed in without the keyword
    options: list
        List of objects to check if `value` is in
    regex: bool, defaults=False
        Informs that the options of the list are regex strings to compare to.
        The `value` is oneof `options` if `value` regex matches to any option.

    Returns
    -------
    True | str
        Returns True if `value` is oneof `options`, otherwise return an error
        message as a string
    """
    value   = var.getValue()
    options = opts or options
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
def isdir(var):
    """
    Simply performs os.path.isdir()

    Parameters
    ----------
    var: mlky.Var
        The Var object to check os.path.isdir(var.value) on

    Returns
    -------
    bool | str
        Returns True if the path exists, otherwise returns an error string
    """
    path = var.getValue()
    if path is Null:
        if var.strict or var.required:
            return f'Directory path not provided'
        else:
            return True
    return os.path.isdir(path) or f'Directory Not Found: {path}'


@register()
def isfile(var):
    """
    Simply performs os.path.isfile()

    Parameters
    ----------
    var: mlky.Var
        The Var object to check os.path.isfile(var.value) on

    Returns
    -------
    bool | str
        Returns True if the path exists, otherwise returns an error string
    """
    path = var.getValue()
    if path is Null:
        if var.strict or var.required:
            return f'File path not provided'
        else:
            return True
    return os.path.isfile(path) or f'File Not Found: {path}'


@register()
def compare(var, lt=None, lte=None, gt=None, gte=None):
    """
    Parameters
    ----------
    var: mlky.Var
        The Var object to compare with
    """
    value  = var.getValue()
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
def between(var, lower, upper, inclusive=False):
    """
    Intuitive syntax for `compare` function

    Parameters
    ----------
    value: any
        The value to compare
    lower: any
        The upper bound comparison
    upper: any
        The upper bound comparison
    inclusive: bool | str, defaults=False
        Boundary inclusivity:
        - False   = Both bounds are exclusive
        - 'lower' = The lower bound is inclusive, upper is not
        - 'upper' = The upper bound is inclusive, lower is not
        - 'both'  = Both bounds are inclusive
        - True    = Both bounds are inclusive

    Returns
    -------
    list | True
        Returns compare(value) with the correct bounds. If `value` is
        within specified bounds, return True, else return a list of strings
        which are the error message(s).
    """
    kwargs = {}
    if inclusive in ['lower', 'both', True]:
        kwargs['gte'] = lower
    else:
        kwargs['gt'] = lower

    if inclusive in ['upper', 'both', True]:
        kwargs['lte'] = upper
    else:
        kwargs['lt'] = upper

    return compare(var, **kwargs)


@register()
def one_valid(items):
    """
    Checks that one of the keys passes .validate()

    Parameters
    ----------
    items: list of Var
        Var objects to validate on

    Returns
    -------
    True | str
        Returns True if one item is valid, otherwise returns an error string

    Notes
    -----
    This is a Sect check function, not be used for Vars
    """
    ov = False # One Valid
    for item in items:
        # Update the Var to ensure checks are properly done
        item._skip_checks = False
        item.strict = True

        # Check if it is valid, record True to OV if any one is
        err = item.validate().reduce()
        ov |= not err

    if ov:
        # All future checks should be skipped as one was valid
        for item in items:
            item._skip_checks = True
        return True

    return f'At least one key must be valid and none are: {[k.name for k in items]}'


@register()
def mutually_exclusive(items):
    """
    Checks that only one key is defined

    Parameters
    ----------
    items: list of Var
        Var objects to validate on

    Returns
    -------
    True | str
        Returns True if one item is valid, otherwise returns an error string

    Notes
    -----
    This is a Sect check function, not be used for Vars
    """
    defined = []
    for item in items:
        if item._f.value is not Null:
            defined.append(item._f.name)

    if len(defined) > 1:
        return f'The following keys are mutually exclusive, please only set one: {defined}'
    return True


@register()
def if_one_then_all(items):
    """
    If one item is defined then all must be defined

    Parameters
    ----------
    items: list of Var
        Var objects to validate on

    Returns
    -------
    True | str
        Returns True if one item is valid, otherwise returns an error string

    Notes
    -----
    This is a Sect check function, not be used for Vars
    """
    defined   = []
    undefined = []
    for item in items:
        name = item._f.name
        if item._f.value is not Null:
            defined.append(name)
        else:
            undefined.append(name)

    if defined and undefined:
        return f'If one is defined, all must be defined: defined={defined}, undefined={undefined}'
    return True
