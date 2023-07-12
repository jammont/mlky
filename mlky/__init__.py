"""
"""
__version__ = '2023.04.0'

# Instantiate before the CLI
from mlky.configs import *

import click

@click.group(invoke_without_command=True, name="config")
@click.pass_context
@click.option("-v", "--version", help="Print the current version of MLky", is_flag=True)
@click.option("-p", "--path", help="Print the installation path of MLky", is_flag=True)
def _cli(ctx, version, path):
    """\
    MLky configuration commands
    """
    if ctx.invoked_subcommand is None:
        if version:
            click.echo(__version__)

        if path:
            click.echo(__path__[0])

from mlky.configs.cli import *

_cli.add_command(click_generate)

class CLI:
    group    = _cli
    generate = click_generate

    @classmethod
    def set_defaults(cls, **kwargs):
        """
        Sets the default values of MLky commands. This allows packages to set
        their own custom values.
        """
        for cmd, defaults in kwargs.items():
            if hasattr(cls, cmd):
                # Retrieve the params for this command
                keys = {param.name: param for param in getattr(cls, cmd).params}
                # Set the default values
                for key, value in defaults.items():
                    keys[key].default = value
