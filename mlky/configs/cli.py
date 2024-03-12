"""
The main CLI for mlky. Presently support the following commands:

```bash
mlky generate -f /some/config.yml -d /some/defs.yml [-s]
mlky validate -f /some/config.yml [-i] -d /some/defs.yml [-di]
```

This CLI can be nested under other Click CLIs via:

```python
# This is your project's CLI (for example)
@click.group(invoke_without_command=True)
@click.pass_context
@click.option("-v", "--version", help="Print the current version", is_flag=True)
@click.option("-p", "--path", help="Print the installation path", is_flag=True)
def cli(ctx, version, path):
    if ctx.invoked_subcommand is None:
        if version:
            click.echo(__version__)

        if path:
            click.echo(__path__[0])


# Import the mlky CLI, set default values for the command such as the defs.yml,
# and set it as a command under your project's CLI
from mlky import CLI as mli

mli.set_defaults(generate={"input": "/path/to/your/projects/definitions.yml"})
cli.add_command(mli.group)
```

This will nest the mlky subcommands under your project's. Assuming your project
was named `mypkg`:

```bash
mpkg generate -f /some/config.yml -d /some/defs.yml [-s]
mpkg validate -f /some/config.yml [-i] -d /some/defs.yml [-di]
```
"""
import click

from . import Config

#%%
@click.group(invoke_without_command=True, name="config")
@click.pass_context
@click.option("-v", "--version", help="Print the current version of MLky", is_flag=True)
@click.option("-p", "--path", help="Print the installation path of MLky", is_flag=True)
def _cli(ctx, version, path):
    """\
    MLky configuration commands
    """
    import mlky

    if ctx.invoked_subcommand is None:
        if version:
            click.echo(mlky.__version__)

        if path:
            click.echo(mlky.__path__[0])

#%%
@_cli.command(name="generate")
@click.option("-f", "--file",
    help    = "File to write the template to",
    default = "generated.yml"
)
@click.option("-d", "--defs",
    help    = "Definitions file",
    default = "defs.yml"
)
@click.option("-clt", "--convertListTypes",
    help    = "Enables converting list types to dicts",
    is_flag = True,
    default = False
)
@click.option("-dmr", "--disableMagicsReplacement",
    help    = "Disables the default behaviour of replacing magics. Disabling this may result in the generated file containing magic strings.",
    is_flag = True,
    default = False
)
def generate(file, defs, convertlisttypes, disablemagicsreplacement):
    """\
    Generates a default config template using the definitions file
    """
    Config._opts.convertListTypes = convertlisttypes
    Config._opts.Var._disable_reset_magics = disablemagicsreplacement

    Config(data={}, defs=defs)
    Config.generateTemplate(file=file)
    click.echo(f"Wrote template configuration to: {file}")

#%%
@_cli.command(name="validate")
@click.option('-f', '--file',
    help         = 'File to validate.',
    required     = True
)
@click.option('-p', '--patch',
    help         = 'Patch to apply'
)
@click.option('-d', '--defs',
    help         = 'Definitions file for validation.',
    required     = True,
    default      = '',
    show_default = True
)
@click.option('-di', '--defs_inherit',
    help         = 'Inheritance to use for the definitions file.',
)
def click_validate(file, inherit, defs, defs_inherit):
    """\
    Validates a configuration file against a definitions file
    """
    click.echo(f'Validation results for {file}:')
    config = Config(file, inherit, defs, defs_inherit, _validate=False)
    errors = config.validate_(_raise=False)
    if not errors:
        click.echo(f'No errors were found.')

#%%
@_cli.command(name="print")
@click.option('-c', '--config',
    help     = 'Configuration file input',
    required = True
)
@click.option('-p', '--patch',
    help     = 'Patch to apply'
)
@click.option('-d', '--defs',
    help     = 'Definitions file to populate the config, if available',
)
@click.option('-t', '--truncate',
    help     = 'Truncates long values for prettier printing',
    type     = int
)
def click_print(config, patch, defs, truncate):
    """\
    Prints the yaml dump for a configuration with a given patch input
    """
    click.echo(f'YAML dump for Config(file={config!r}, patch={patch!r}, defs={defs!r})')
    Config(config, patch, defs)
    dump = Config.dumpYaml(truncate=truncate)
    click.echo(dump)

#%%
class CLI:
    """
    This class enables access to otherwise private mlky CLI functions. If
    changes need to happen, import this class and use the attributes
    """
    group    = _cli
    generate = generate

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

#%%
