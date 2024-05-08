"""
Handles the magics syntax mlky defines
"""
import logging
import re

from . import (
    Config,
    funcs,
    magic_regex,
    Null,
    register,
    Var
)


Logger = logging.getLogger(__file__)


def _debug(lvl, name, msg):
    """
    """
    if lvl == 'e':
        Logger.error(msg)
    else:
        Logger.warning(msg)


@register(name='config.replace')
def replace(value, instance=None, dtype=None, callResets=False, _debug=_debug):
    """
    Replaces format signals in strings with values from the config relative to
    its inheritance structure.

    Parameters
    ----------
    value: str
        Matches roughly to ${config.*} in the string and replaces them with the
        corrosponding config value. See notes the regex for accuracy.
    instance: Sect, defaults=None
        Instance to use for value lookups. Defaults to the global instance
    dtype: any, defaults=None
        Data type to attempt casting the replacement value to
    callResets: bool, defaults=False
        Calls reset on retrieved Vars. Warning: This may cause a recursive loop. Experimental.
    _debug: function
        Sect or Var ._debug() function for debug logging

    Returns
    -------
    value: any
        Replaced value

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
        # Special case for special Null syntax
        if value == '\\':
            return Null

        matches = re.findall(magic_regex, value)

        for match in matches:
            # Config lookup case
            if match.startswith('.'):
                keys = match.split('.')

                if len(keys) < 2:
                    _debug('e', 'replace', f'Keys path provided is invalid, returning without replacement: {keys!r}')
                    return value

                data = instance or Config
                for key in keys[1:]:
                    data = data.get(key, other=Null, var=True)

                if isinstance(data, Var):
                    if callResets:
                        _debug(0, 'replace', f'Calling Var.replace from magics.replace on {data.name}')
                        data.switchReplace()

                    data = data.getValue()

                if isinstance(data, Null):
                    _debug(0, 'replace', f'Lookup({match}) returned Null. This may not be expected and may cause issues.')

            # Environment variable lookup case
            elif match.startswith('$'):
                data = funcs.getRegister('get_env')(match[1:])

            # Lookup custom function case
            elif match.startswith('?'):
                data = funcs.getRegister(match[1:])()

            # Data lookup case
            elif match.startswith('!'):
                return funcs.getRegister(match[1:])()

            else:
                _debug(0, 'replace', f'Replacement matched to string but no valid starter token provided: {match!r}')

            if data is not Null:
                value = value.replace('${'+ match +'}', str(data))

    if dtype:
        return cast(value, dtype, _debug)

    return value


@register(name='config.cast')
def cast(value, dtype, _debug=_debug):
    """
    Attempts to cast a value to a given dtype

    Parameters
    ----------
    value: any
        Value to cast
    dtype: type
        Type to cast with
    _debug: function
        Sect or Var ._debug() function for debug logging

    Returns
    -------
    value: any
        Casted value if possible, otherwise the original value
    """
    if isinstance(dtype, list):
        _debug(0, 'replace', f'Cannot cast replacement value {value!r} as the dtype is a list and cannot be assumed: {dtype=}')

    elif dtype in (list, tuple):
        # Logger.debug(f'List dtype casting is not supported')
        pass

    # Skip casting on these dtypes
    elif dtype in ('any', 'None', None, 'Null', Null):
        pass

    # Skip casting on these values
    elif value in (Null, None):
        pass

    else:
        try:
            value = dtype(value)
        except:
            _debug('e', 'replace', f'Failed to cast replacement value {value!r} to {dtype=}')

    return value


@register(name='config.addChecks')
def addChecks():
    """
    Adds checks that were assigned by a registered function to the Config
    """
    Config._log(0, 'addChecks', 'Adding checks to Config')
    for key, checks in funcs.Checks.items():
        lvls = key.split('.')[1:]

        # Find the key of interest
        this = Config
        for lvl in lvls:
            this = this.get(lvl, Null, var=True)

        # Assign the check if the key exists
        if this:
            this._f.checks += checks
            Logger.debug(f'└ {this}._f.checks += {checks}')
