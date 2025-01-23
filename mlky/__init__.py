"""
"""
import importlib.metadata

__version__ = importlib.metadata.version("mlky")

# Instantiate before the CLI
from .configs import *
from .        import cli
