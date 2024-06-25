"""
Order of operations matter due to dependencies
"""
from .null import (
    Null,
    NullDict
)

# Disable Null warnings during initialization
Null._warn = False

from .      import funcs
from .funcs import (
    ErrorsDict,
    register
)

from .sect import Sect
from .base import BaseSect
from .dict import DictSect
from .list import ListSect
from .var  import Var

from . import builtins

from .interpolate import (
    MAGIC,
    interpolate,
    lookup
)

# Re-enable at the end
Null._warn = True

# Global config object, used as a singleton
Config = Sect()
