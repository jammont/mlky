"""
The main CLI for mlky. Presently support the following commands:

```bash
mlky generate -f /some/config.yml -d /some/defs.yml [-s]
mlky validate -f /some/config.yml [-i] -d /some/defs.yml [-di]
```

This CLI can be nested under other Click CLIs via:

```python
# This is your project's CLI (for example)
@click.group(name='mypkg')
def cli():
    ...

# Import mlky, set some defaults, and add the mlky commands to your cli
import mlky

defs = '/some/defs.yml'
mlky.cli.setDefaults(defs=defs)

cli.add_command(mlky.cli.commands)
```

This will nest the mlky subcommands under your project's. Assuming your project
was named `mypkg`:

```bash
mypkg generate -f /some/config.yml -d /some/defs.yml
mypkg validate -c /some/config.yml -d /some/defs.yml
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
debug = createOption(['--debug'], {
    'type': int,
    'help': 'Sets the mlky debug flag'
})


@click.group(invoke_without_command=True, name="config")
@click.pass_context
@click.option("-v", "--version", help="Print the current version of MLky", is_flag=True)
@click.option("-p", "--path", help="Print the installation path of MLky", is_flag=True)
def commands(ctx, version, path):
    """\
    MLky configuration commands
    """
    import mlky

    if ctx.invoked_subcommand is None:
        if version:
            click.echo(mlky.__version__)

        if path:
            click.echo(mlky.__path__[0])


@commands.command(name="generate")
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
    Config(_defs=defs, _override=override)

    Config.toYaml(file=file, listStyle=liststyle)

    click.echo(f"Wrote template configuration to: {file}")


@commands.command(name="validate")
@config
@patch
@defs
@override
@debug
def validate(config, patch, defs, override, debug):
    """\
    Validates a configuration file against a definitions file
    """
    click.echo(f'Validation results for {config}:')

    if debug:
        Config.enableLogging()

    Config(config, _patch=patch, _defs=defs, _override=override, _debug=debug)

    valid = Config.validateObj()
    if valid:
        click.echo(f'No errors were found.')


@commands.command(name="print")
@config
@patch
@defs
@override
@liststyle
@debug
@click.option('-t', '--truncate',
    help = 'Truncates long values for prettier printing',
    type = int
)
def report(config, patch, defs, override, liststyle, debug, truncate):
    """\
    Prints the yaml dump for a configuration with a given patch input
    """
    click.echo(f'[Config]' + '='*100)

    if debug:
        Config.enableLogging()

    Config(config, _patch=patch, _defs=defs, _override=override, _debug=debug)

    click.echo(Config.toYaml(listStyle=liststyle, truncate=truncate, comments=None))

    click.echo('-'*109)


def setDefaults(**kwargs):
    """
    Set default values for specific command parameters or all command parameters.

    Defaults for all commands should precede defaults for specific commands in the
    parameters (kwargs). See examples.

    Parameters
    ----------
    **kwargs : dict
        Key-value pairs where the key is the command name or parameter name, and the
        value is a dictionary of parameter defaults for specific commands or a single
        default value for all commands.

    Raises
    ------
    AttributeError
        If a default value for a specific command is not provided as a dictionary.

    Examples
    --------
    >>> import mlky
    >>> # Set defaults for all commands
    >>> mlky.cli.setDefaults(defs='abc')
    >>> mlky.cli.commands.commands['generate'].params[1].default
    'abc'
    >>> mlky.cli.commands.commands['validate'].params[2].default
    'abc'
    >>> # Set defaults for all commands, then change the default specifically for one command
    >>> setDefaults(defs='abc', validate={'defs': 'xyz'})
    >>> mlky.cli.commands.commands['generate'].params[1].default
    'abc'
    >>> mlky.cli.commands.commands['validate'].params[2].default
    'xyz'
    >>> # If specific defaults precede global defaults, the globals will overwrite the specific
    >>> setDefaults(validate={'defs': 'xyz'}, defs='abc')
    >>> mlky.cli.commands.commands['generate'].params[1].default
    'abc'
    >>> mlky.cli.commands.commands['validate'].params[2].default
    'abc'
    """
    # Retrieve the commands from the mlky click group object
    cmds = commands.commands

    for key, default in kwargs.items():
        # Retrieve a command and update those params only
        cmd = cmds.get(key)
        if cmd:
            if not isinstance(default, dict):
                raise AttributeError(f'Setting defaults for a specific command must be a dict. Got type {type(default)}: {key!r}={default!r}')

            # Retrieve the params for this command
            params = {param.name: param for param in cmd.params}

            # Set the default values
            for opt, val in default.items():
                params[opt].default = val

        # Or update all commands' defaults
        else:
            for cmd in cmds.values():
                params = {param.name: param for param in cmd.params}
                opt = params.get(key)

                if opt:
                    opt.default = default
