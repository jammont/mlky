"""
"""
import logging

from . import Null


Logger = logging.getLogger(__file__)

# {key: func}, all registered functions of mlky
Funcs = {}

# Tracks which Config keys need to update their _f.checks list after initialization
Checks = {}


class ErrorsDict(dict):
    """
    Assists the Sect and Var .validate() functions by enabling an easy way to
    clean up the final error report dict for easier parsing. This will also
    assist in resolving return type issues with custom functions by enforcing
    their return types to only be strings or lists.
    """
    def reduce(self):
        reduced = ErrorsDict()
        for key, val in self.items():
            if isinstance(val, ErrorsDict):
                new = val.reduce()
                if new:
                    reduced[key] = new
            elif isinstance(val, (str, list)):
                reduced[key] = val
        return reduced


def register(key='', name=None, regex=False, **kwargs):
    """
    Registers a function with mlky to be used either in a definitions file or
    assigned directly as a check for a given key
    """
    def wrap(func):
        """
        Wraps the registered function
        """
        def protect(*args, **kwargs):
            """
            Protects from exceptions as well as enables the original `func` to
            be directly callable
            """
            try:
                return func(*args, **kwargs)
            except Exception as e:
                Logger.exception(f'Register {name!r} raised an exception:')
                Logger.warning('Returning the exception message. This may cause unintended behaviour.')
                return str(e)

        # Either the function name or an assigned one
        nonlocal name
        name = name or func.__name__

        if name in Funcs:
            Logger.warning(f'Function is already registered and will be replaced: {name!r}')

        # This check will be assigned to a specific key
        if key.startswith('.'):
            Checks.setdefault(key, []).append(name)

        # Register the function
        Funcs[name] = protect
        Logger.debug(f'Registered function {name!r}')

        return protect

    return wrap


def getRegister(key):
    """
    Retrieves a function from the registers list
    """
    if key not in Funcs:
        # Magic functions initialize at the end of mlky, don't report an error if these don't exist yet
        if not key.startswith('config.'):
            Logger.error(f'The following key is not a registered function, returning Null which may have unintended consequences: {key!r}')
        return Null
    return Funcs[key]
