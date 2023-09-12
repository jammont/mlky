"""
"""
import logging
import os

from . import Null


Logger = logging.getLogger('mlky/functions')


class Functions:
    """
    The Functions class holds all of the registered functions of MLky and the
    logic to handle them. These registered functions include type checks,
    builtins.py, and custom functions.

    Usage:
    >>> from mlky import register, Functions
    >>> @register(key="funcName")
    ... def someFunc(val):
    ...   return isinstance(val, int)
    >>> Functions.check(1)
    True
    >>> Functions.check('1')
    False
    """
    funcs = {}

    @classmethod
    def check(cls, key, val=None, *args, **kwargs):
        """
        Executes a registered function on a value.

        Parameters
        ----------
        key: str
            Key name of the function to retrieve
        val: any, default=None
            Value to execute the registered function on
        *args: any
            List of positional arguments to pass to the registered function
        **kwargs: any
            Dict of keyword arguments to pass to the registered function

        Returns
        -------
        any
            Returns the return of the registered function
        """
        if key not in cls.funcs:
            return f'Check {key!r} is not registered'
        return cls.funcs[key](val, *args, **kwargs)

    @classmethod
    def get(cls, key, other=None):
        return cls.funcs.get(key, other)

    @classmethod
    def register(cls, key, func, example=None):
        """
        Registers a custom function to be used by the `check` function.

        Additionally protects from exceptions.
        """
        def protect(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                Logger.exception(f'Register {key} raised an exception:')
                Logger.warning('Returning the exception message. This may cause unintended behaviour.')
                return str(e)

        if key in cls.funcs:
            Logger.warning(f'Function {key}')

        cls.funcs[key] = protect


def register(key=None):
    """
    Register function that can be used as a decorator. Passes the function
    along to Functions.register

    Parameters
    ----------
    key: str, default=None
        The key name to register the function as. If None, will use
        function.__name__
    """
    def decorator(function):
        Functions.register(key or function.__name__, function)

        return function
    return decorator


# Builtin provided type functions. More types can be added by importing this dict and appending to it
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

@register('type')
def check_type(value, dtype):
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
        else:
            return True

    # Try a builtin then fallback to custom registered
    func = Types.get(dtype, Functions.get(dtype))
    if func is None:
        return f'Unknown type: {dtype!r}'

    ret = func(value)
    if ret is True:
        return True
    if isinstance(ret, (str, list)):
        return ret
    else:
        return f'Wrong type: Expected <{dtype!r}> Got {type(value)}'
