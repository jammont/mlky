"""
Order of operations matter due to dependencies
"""
# Independent
from .null import Null

# Dependent on Null
from .functions import (
    Functions,
    register
)

# Dependent on Null, Functions
from .var import Var

# Dependent on Null, Functions, register
from . import builtins

# Dependent on Null, Functions, Var
from .sect import Sect

# Dependent on Sect
from .definitions import generate

# Dependent on Null, Functions, register, Var, Sect
from .config import Config

# Dependent on Null, Functions, register, Config
from . import magics
