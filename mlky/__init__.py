"""
"""
import importlib.metadata

__version__ = "4.2.5"

# Instantiate before the CLI
from .configs import *
from .        import cli
