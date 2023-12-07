"""
Houses all of the built-in register functions of mlky. These are generalized
functions that may be applicable to a wide variety of use cases.
"""
import os
import re
import uuid

from . import (
    funcs,
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


@register()
def oneof(var, *options, regex=False):
    """
    Checks if a given value is one of a list of options

    Parameters
    ----------
    var: mlky.Var
        Checks the var.value against `options`
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
    value = var.value
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
    bool or str
        Returns True if the path exists, otherwise returns an error string
    """
    path = var.value
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
    bool or str
        Returns True if the path exists, otherwise returns an error string
    """
    path = var.value
    return os.path.isfile(path) or f'File Not Found: {path}'


@register()
def compare(var, lt=None, lte=None, gt=None, gte=None):
    """
    Parameters
    ----------
    var: mlky.Var
        The Var object to compare with
    """
    value  = var.value
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
def between(var, a, b, inclusive=False):
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
    kwargs = {}
    if inclusive in ['lower', 'both', True]:
        kwargs['gte'] = a
    else:
        kwargs['gt'] = a

    if inclusive in ['upper', 'both', True]:
        kwargs['lte'] = b
    else:
        kwargs['lt'] = b

    return compare(var, **kwargs)


@register()
def one_valid(items):
    """
    Checks that one of the keys passes .validate()
    """
    ov = False # One Valid
    for item in items:
        err = item.validate().reduce()
        ov |= not err
    return ov or f'At least one key must be valid and none are: {keys}'


@register()
def mutually_exclusive(items):
    """
    Checks that only one key is defined
    """
    defined = []
    for item in items:
        if item._f.value is not Null:
            defined.append(item._f.name)

    if len(defined) > 1:
        return f'The following keys are mutually exclusive, please only set one: {defined}'
    return True


## Builtin provided type functions
# More types can be added by importing this dict and appending to it
# Or by registering a function with the same name as the type
Types = {
    Null     : lambda value: True,
    'Null'   : lambda value: True,
    None     : lambda value: True,
    'None'   : lambda value: True,
    'any'    : lambda value: True,
    'bool'   : lambda value: isinstance(value, bool   ),
    'bytes'  : lambda value: isinstance(value, bytes  ),
    'complex': lambda value: isinstance(value, complex),
    'dict'   : lambda value: isinstance(value, dict   ),
    'float'  : lambda value: isinstance(value, float  ),
    'int'    : lambda value: isinstance(value, int    ),
    'list'   : lambda value: isinstance(value, list   ),
    'set'    : lambda value: isinstance(value, set    ),
    'str'    : lambda value: isinstance(value, str    ),
    'tuple'  : lambda value: isinstance(value, tuple  )
}

@register()
def check_dtype(value, dtype):
    """
    Checks the type of a given value.

    Parameters
    ----------
    value: any
        The value in question
    dtype: any
        The type this value is supposed to be. If type in [Null, 'Null', None,
        'None', 'any'] then the check is disabled and will return True.
        Otherwise, uses the Types dictionary to lookup the function to validate
        with.

    Returns
    -------
    True or str or list of str
        Returns True if this value is the expected type. If it is not, returns
        either a string or list of strings describing the error.
    """
    if isinstance(dtype, list):
        if True not in [check_type(value, t) for t in dtype]:
            return f'Value type <{dtype!r}> is not one of {dtype}'
        return True

    # Try a builtin then fallback to custom registered
    func = Types.get(dtype, funcs.Funcs.get(dtype))
    if func is None:
        return f'Unknown type: {dtype!r}'

    ret = func(value)
    if ret is True:
        return True
    if isinstance(ret, (str, list)):
        return ret
    else:
        return f'Wrong type: Expected <{dtype!r}> Got {type(value)}'
