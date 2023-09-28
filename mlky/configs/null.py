"""
The Null class of mlky.
"""
import logging


Logger = logging.getLogger('__file__')


class NullType(type):
    """
    Acts like a Nonetype (generally) without raising an exception in common use
    cases such as:
    - __getattr__, __getitem__ will return itself, preventing raising missing
    attribute. Ex: config.this_key_is_missing.also_missing will return Null.
    - Dict functions .get, .keys, and .items will return empty lists/dicts.
    - Comparisons should always return False unless compared to a None or Null
    type.

    Warnings can be disabled via:
    >>> Null._warn = False
    """
    _warn = True

    def __call__(cls, *args, **kwargs):
        return cls

    def __deepcopy__(self, memo):
        return type(self)()

    def __hash__(cls):
        return hash(None)

    def __bool__(cls):
        return False

    def __contains__(cls):
        return False

    def __eq__(cls, other):
        return type(other) in [type(None), type(cls)]

    def __setattr__(cls, key, value):
        if key == '_warn':
            super().__setattr__(key, value)
        elif cls._warn:
            Logger.warning(f'{cls.__name__} objects cannot take attribute assignments but will not raise an exception')

    def __getattr__(cls, key):
        return cls

    def __setitem__(cls, key, value):
        setattr(cls, key, value)

    def __getitem__(cls, key):
        return cls

    def __str__(cls):
        return 'Null'

    def __repr__(cls):
        return 'Null'

    def get(self, key, other=None):
        return other

    def keys(self):
        return []

    def items(self):
        return ()


class Null(metaclass=NullType):
    ...
