"""
Data types module
"""
import pathlib

from .null import Null


class Types:
    """
    Data Types base class
    """
    @classmethod
    def __eq__(self, other):
        return self.label == other


    @classmethod
    def istype(cls, value):
        return isinstance(value, cls.dtype)


    @classmethod
    def cast(cls, value):
        # Auto convert \ to Null
        if value == '\\':
            return Null

        # Don't cast these types
        if value in (Null, None):
            return value

        return cls.dtype(value)


    @classmethod
    def yaml(cls, value):
        # Nulls dump as \
        if value is Null:
            return '\\'

        return str(value)


class Any(Types):
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


class Str(Types):
    label = 'str'
    dtype = str

    @classmethod
    def yaml(cls, value):
        value = super().yaml(value)
        if value == '':
            return '""'
        return value


class Int(Types):
    label = 'int'
    dtype = int


class Bool(Types):
    label = 'bool'
    dtype = bool


class Float(Types):
    label = 'float'
    dtype = float


class Bytes(Types):
    label = 'bytes'
    dtype = bytes


class Path(Types):
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
