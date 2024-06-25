"""
Data types module
"""
import pathlib

from .null import Null


class Types(type):
    """
    Data Types metaclass
    """
    def __eq__(cls, other):
        # "*" matches to all dtypes
        if isinstance(other, str) and other == '*':
            return True
        return cls.label == other


    def __hash__(cls):
        return hash(cls.label)


    def istype(cls, value):
        return isinstance(value, cls.dtype)


    def cast(cls, value):
        # Auto convert \ to Null
        if value == '\\':
            return Null

        # Don't cast these types
        if value in (Null, None):
            return value

        return cls.dtype(value)


    def yaml(cls, value):
        # Nulls dump as \
        if value is Null:
            return '\\'

        return str(value)


class Any(metaclass=Types):
    label = 'any'
    dtype = Null

    @classmethod
    def __eq__(self, other):
        # Match to a Var type, not DictSect or ListSect
        return other not in ('dict', 'list')


    @classmethod
    def istype(cls, value):
        return True


    @classmethod
    def cast(cls, value):
        return value


class Str(metaclass=Types):
    label = 'str'
    dtype = str

    @classmethod
    def yaml(cls, value):
        value = Types.yaml(cls, value)
        if value == '':
            return '""'
        return value


class Int(metaclass=Types):
    label = 'int'
    dtype = int


class Bool(metaclass=Types):
    label = 'bool'
    dtype = bool


class Float(metaclass=Types):
    label = 'float'
    dtype = float


class Bytes(metaclass=Types):
    label = 'bytes'
    dtype = bytes


class Path(metaclass=Types):
    label = 'path'
    dtype = pathlib.Path

    @classmethod
    def cast(cls, value):
        if value is Null:
            return '\\'

        return cls.dtype(str(value))


# Define what keys would match to which dtype class
dtypes = {
# class: [keys, ]
    Str: (Str, str, 'str', 'string'),
    Int: (Int, int, 'int', 'integer'),
    Bool: (Bool, bool, 'bool', 'boolean'),
    Float: (Float, float, 'float'),
    Bytes: (Bytes, bytes, 'bytes'),
    Path: (Path, pathlib.Path, 'Path', 'path'),
}

# Convert into a hashmap
dtypes = {key: cls for cls, keys in dtypes.items() for key in keys}


def getType(dtype):
    """
    Get the correct dtype class. Defaults to Any if the input does not match to a class

    Parameters
    ----------
    dtype : type or str
        Dtype to retrieve

    Returns
    -------
    class
        Corresponding dtype class
    """
    return dtypes.get(dtype, Any)
