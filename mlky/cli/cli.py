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
mypkg generate -f /some/config.yml -d /some/defs.yml [-s]
mypkg validate -f /some/config.yml [-i] -d /some/defs.yml [-di]
```
"""
import click

from ..configs import Config


def createOption(flags, opts):
    """
    Creates a Click option decorator that can be used with or without parameters.

    Parameters
    ----------
    flags : tuple
        A tuple containing the flags for the Click option (e.g., ('--flag', '-f')).
    opts : dict
        A dictionary containing the option settings (e.g., {'help': 'Description of the option'}).

    Returns
    -------
    function
        A decorator function that can be used to add the Click option to another function.
    """
    def clickOption(*args, **kwargs):
        def wrap(func):
            return click.option(*flags, **(opts|kwargs))(func)

        if args and callable(args[0]):
            return wrap(args[0])

        return wrap

    return clickOption

# Shared click options
config    = createOption(['-c', '--config'], {
    'required': True,
    'help': 'Path to a mlky configuration file'
})
patch     = createOption(['-p', '--patch'], {
    'help': 'Patch order for mlky'
})
defs      = createOption(['--defs'], {
    'help': 'Path to a mlky definitions file'
})
override  = createOption(['-o', '--override'], {
    'type': (str, str),
    'multiple': True,
    'help': 'Override config keys'
})
liststyle = createOption(['-ls', '--liststyle'], {
    'type': click.Choice(['short', 'long']),
    'default': 'short',
    'help': 'Sets the list style for the toYaml function'
})


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


@_cli.command(name="generate")
@click.option("-f", "--file",
    help    = "File to write the template to",
    default = "generated.yml"
)
@defs
@override
@liststyle
def generate(file, defs, override, liststyle):
    """\
    Generates a default config template using the definitions file
    """
    Config(_defs=defs)

    for key, value in override:
        Config.overrideKey(key, value)

    Config.toYaml(file=file, listStyle=liststyle)

    click.echo(f"Wrote template configuration to: {file}")


@_cli.command(name="validate")
@config
@patch
@defs
@override
def validate(config, patch, defs, override):
    """\
    Validates a configuration file against a definitions file
    """
    click.echo(f'Validation results for {file}:')
    Config(file, _patch=patch, _defs=defs)

    for key, value in override:
        Config.overrideKey(key, value)

    errors = Config.validate()
    if not errors:
        click.echo(f'No errors were found.')


@_cli.command(name="print")
@config
@patch
@defs
@override
@liststyle
@click.option('-t', '--truncate',
    help = 'Truncates long values for prettier printing',
    type = int
)
def report(config, patch, defs, override, liststyle, truncate):
    """\
    Prints the yaml dump for a configuration with a given patch input
    """
    click.echo(f'[Config]' + '='*100)

    Config(config, _patch=patch, _defs=defs)

    for key, value in override:
        Config.overrideKey(key, value)

    click.echo(Config.toYaml(listStyle=liststyle, truncate=truncate))

    click.echo('-'*109)


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
