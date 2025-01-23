"""
"""
import importlib.metadata

__version__ = importlib.metadata.version("mlky")

# Instantiate before the CLI
from mlky.configs import *
from mlky         import cli
