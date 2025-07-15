"""
"""
import importlib.metadata

__version__ = "4.2.8"

# Instantiate before the CLI
from .configs import *
from .        import cli
