"""
The `configs` module contains the core of mlky. Most notably, the `Config` object is
created on loading the mlky package which is the primary entry point to getting
started. See the [Getting Started](../../../usage.md) guide for more information.
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
