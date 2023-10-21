"""
Order of operations matter due to dependencies
"""
# Independent
from .null import (
    Null,
    NullDict,
    NullType
)

# Dependent on Null
from .functions import (
    Functions,
    register
)

# Dependent on Null, Functions
from .var import Var

# Dependent on Null, Functions, register
from . import builtins

# Dependent on Null, NullDict, NullType, Functions, Var
from .sect import Sect

# Dependent on Sect, NullDict
from .definitions import generate

# Dependent on Null, NullDict, Functions, register, Var, Sect
from .config import Config

# Dependent on Null, Functions, register, Config
from . import magics
