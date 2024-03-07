"""
Order of operations matter due to dependencies
"""
# Regex string for matching to mlky magics
magic_regex = r"\${([\.\$\!].*?)}"

# Independent
from .null import (
    Null,
    NullDict,
    NullType
)

# Disable Null warnings during initialization
Null._warn = False

# Dependent on Null
from .      import funcs
from .funcs import (
    ErrorsDict,
    register
)

# Dependent on Null, ErrorsDict, funcs
from .var import Var

# Dependent on Null, funcs, register
from . import builtins

# Dependent on Null, NullDict, NullType, ErrorsDict, funcs, Var
from .sect import Sect

# Dependent on Sect, NullDict
from .definitions import generate

# Dependent on Null, NullDict, funcs, register, Var, Sect
from .config import GlobalConfig as Config

# Dependent on Null, funcs, register, Config
from . import magics

# Re-enable at the end
Null._warn = True
