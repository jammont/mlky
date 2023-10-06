"""
Handles the magics syntax mlky defines
"""
import logging
import re

from . import (
    Config,
    Null,
    Functions,
    register
)


Logger = logging.getLogger(__file__)


@register('config.replace')
def replace(value):
    """
    Replaces format signals in strings with values from the config relative to
    its inheritance structure.

    Parameters
    ----------
    value: str
        Matches roughly to ${config.*} in the string and replaces them with the
        corrosponding config value. See notes the regex for accuracy.

    Returns
    -------
    string: str
        Same string but with the values replaced.

    Notes
    -----
    The regex used for matching is r"\${([\.\$].*?)}". This will match to any
    string starting with `.` or `$` wrapped by `${}`. Reasons to only match
    starting with specific keys is to:
        - `.` - Config value lookup
        - `$` - Environment variable lookup

    Config references must be relative to the inheritance structure. With
    inheritance, the top level sections do not exist. Without inheritance, they
    do. Examples:

    >>> # Without inheritance
    >>> config = Config('''
    default:
        path: /abc
        vars:
            x: 1
            y: 2
    foo:
        file: ${.default.path}/${.default.vars.x}/${.default.vars.y}
    ''')
    >>> replace(config.foo.file)
    '/abc/1/2'

    >>> # With inheritance
    >>> config = Config('''
    default:
        path: /abc
        vars:
            x: 1
            y: 2
    foo:
        file: ${.path}/${.vars.x}/${.vars.y}
    ''', 'default<-foo')
    >>> replace(config.file)
    '/abc/1/2'
    """
    if isinstance(value, str):
        matches = re.findall(r"\${([\.\$\!].*?)}", value)

        for match in matches:
            # Config lookup case
            if match.startswith('.'):
                keys = match.split('.')

                if len(keys) < 2:
                    Logger.error(f'Keys path provided is invalid, returning without replacement: {keys!r}')
                    return value

                data = Config()
                for key in keys[1:]:
                    data = data.__getattr__(key)

                if isinstance(data, Null):
                    Logger.warning(f'Lookup({match}) returned Null. This may not be expected and may cause issues.')

            # Environment variable lookup case
            elif match.startswith('$'):
                data = Functions.check('get_env', match[1:])

            # Lookup custom function case
            elif match.startswith('?'):
                data = Functions.check(match[1:])

            # Data lookup case
            elif match.startswith('!'):
                return Functions.check(match[1:])

            else:
                Logger.warning(f'Replacement matched to string but no valid starter token provided: {match!r}')

            value = value.replace('${'+ match +'}', str(data))

    return value
