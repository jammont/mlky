"""
"""
import importlib.metadata

__version__ = "4.2.7"

# Instantiate before the CLI
from .configs import *
from .        import cli
