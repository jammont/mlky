"""
Interpolate values in a string
"""
import re

from .base  import isSectType
from .funcs import getRegister
from .null  import Null


# Regex magic pattern
MAGIC = r'\${([^}]*)\}'


def lookup(string, relative, absolute=None, var=False, print=print):
    """
    Performs a lookup on Sect objects by traversing the _parent objects tree using
    either a relative path or the absolute path from the root parent

    Parameters
    ----------
    string : str
        Key string to look up
    relative : SectType
        The relative path starting point
    absolute : SectType, default=None
        The absolute path starting point. If None, the relative path is used as the
        absolute path as well
    var : bool, default=False
        If true, retrieve Var objects themselves, else return the value of the Var
    print : function, default=print
        The reporting function

    Returns
    -------
    obj : any
        The value at key
    """
    if absolute is None:
        absolute = relative

    parts = string.split('.')

    # Index of parts to start referencing on, used in the relative case to skip the blanks
    i = 0

    # Discover relative instance
    if string.startswith('.'):
        print('Using relative pathing')
        obj = relative
        for i, part in enumerate(parts):
            if part == '':
                obj = obj._parent

                if obj is None:
                    print('Cannot find reference object for interpolation')
                    return Null
            else:
                break
    # Not relative, use the root path
    else:
        print('Using absolute pathing')
        obj = absolute

    for part in parts[i:]:
        print(f'Retrieving {part} on {obj}')

        if isSectType(obj, 'list'):
            if part.isnumeric():
                part = int(part)
            else:
                print('References on list sections must be an integer')

        elif obj is Null:
            print('Lookup reference was Null')
            return Null

        obj = obj.get(part, var=var)

    return obj


def interpolate(string, instance, print=print, relativity=True):
    """
    Interpolates a value from a string. An interpolation key in a string starts with
    '${' and ends with '}'. The following rules are currently implemented:

    - ${!abc} = Return a function call named `abc`
    - ${?abc} = Replace this value in the string with the return of the function named
                `abc`
    - ${.abc} = Lookup the key `abc` relative to this instance. Relatives are:
        `.`   = Sibling
        `..`  = Parent
        `...` = Grandparent, etc
    - ${abc}  = Lookup the key `abc` from the root node of this instance

    Parameters
    ----------
    string : str
        String to interpolate
    instance : SectType
        The instance this string derives from. This is used to discover the root node
    print : function, default=print
        The print function to use for reporting. Can be replaced with functions like
        logging.getLogger().debug to output messages to DEBUG, for instance
    relativity : bool, default=True
        Allows relativity lookups. If False, disables the ${.abc} case by removing the
        leading '.'

    Returns
    -------
    varies
        Interpolated string if not a function call case, otherwise the return of the
        function
    """
    root = instance
    while root._parent:
        root = root._parent

    if not relativity:
        string = string.replace('${.', '${')

    matches = re.findall(MAGIC, string)
    for match in set(matches):
        # Reconstruct the matched substring
        sub = '\${'+match+'}'

        # Environment variable lookup case
        if match.startswith('$'):
            print(f'Environment lookup: {match}')
            value = getRegister('get_env')(match[1:])

        # Return function call directly case
        elif match.startswith('!'):
            print(f'Function call: {match}')
            return getRegister(match[1:])()

        # Lookup custom function case
        elif match.startswith('?'):
            print(f'Function lookup: {match}')
            value = getRegister(match[1:])()

        # Lookup a key on the Sect
        else:
            print(f'Key lookup: {match}')
            value = lookup(match, relative=instance, absolute=root, print=print)

        # No lookup was found, leave as-is
        # NOTE: This allows Nonetypes to still passthrough
        if value is Null:
            continue

        # Entire string replaced by this value
        # [1:] to skip the added \
        if sub[1:] == string:
            print('Returning single-value lookup')
            return value

        if isSectType(value, ['dict', 'list']):
            print('Lookup was a Sect object, refusing replacement to avoid recursion')
            continue

        # Replacement must be string
        value = str(value)

        print(f'Replacing {match!r} with {value!r}')

        # Handle backslash edgecase causing issues with re.sub
        if value == '\\':
            value = r'\\'

        # Otherwise replace in place
        string = re.sub(sub, value, string)

    return string
