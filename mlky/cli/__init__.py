"""
mlky comes with a [click](https://click.palletsprojects.com/en) CLI that is designed to
easily integrate with other click CLIs. The following commands are provided
out-of-the-box and immediately available once mlky is installed:

```bash
mlky generate
mlky validate
mlky print
```

Add `--help` to each of the above commands to view usage instructions.

## Subcommands

These commands can be added as subcommands to other click CLIs to abstract away the
mlky command and/or to set defaults for the commands. For example:

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

This will nest the mlky subcommands under your project's CLI. Assuming your project
was named `mypkg`, these commands are now accessible via:

```bash
mypkg generate ...
mypkg validate ...
mypkg print ...
```

## Common click options

Several click options that are commonly used may be imported and either used as-is or
modified for specific use-cases. The following click options are available:

Option    | Flags                | Description                                 | Default Parameters
------    | -----                | -----------                                 | ------------------
config    | `-c`, `--config`     | Path to a mlky configuration file           | `required=True`
patch     | `-p`, `--patch`      | Patch order for mlky                        |
defs      | `--defs`             | Path to a mlky definitions file             |
override  | `-o`, `--override`   | Override config keys                        | `multiple=True`
liststyle | `-ls`, `--liststyle` | Sets the list style for the toYaml function | `type=click.Choice(['short', 'long']), default='short'`
debug     | `--debug`            | Sets the mlky debug flag                    | `type=int`
nointerp  | `-ni`, `--nointerp`  | Disables interpolation                      | `is_flag=True`

These can be used to create custom functions, for example a config initializer:

```python
@mlky.cli.config
@mlky.cli.patch
@mlky.cli.defs(default="/path/to/some/defs.yml")
@mlky.cli.override
def initConfig(config, patch, defs, override):
    C(config, _patch=patch, _defs=defs, _override=override)
```

Notice that the `defs` command is given a `default` parameter. Any additional
parameters provided will override the default set by mlky.

Another example, to disable the `required` flag of `--config`:

```python
@mlky.cli.config(required=False)
def initConfig(config):
    ...
```

"""
from .cli import (
    commands,
    config,
    patch,
    defs,
    override,
    setDefaults
)
