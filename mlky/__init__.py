"""
"""
import importlib.metadata

__version__ = importlib.metadata.version("mypackage")

# Instantiate before the CLI
from mlky.configs import *
from mlky         import cli
