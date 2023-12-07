"""
Utilities for the `definitions` files
"""
from . import NullDict
from ..utils import (
    printTable,
    load_string
)


Comments = {
    'default': ('default:', '?', 'Type', 'Default options across all scripts'),
    'list section': ('', '', 'This is a list of dictionary section. There can be multiple entries of the following keys using `-` to separate entries.'),
    'header': """\
# mlky uses special syntax ${?key} to perform value replacement operations at runtime:
#   ${.key} - Replace this ${} in the string with the value at config[key]
#   ${$key} - Replace this ${} in the string with the environment variable `key`
#   ${?key} - Replace this ${} in the string with the str(return) from function `key` in the registered functions
#   ${!key} - Replace this value with the return from function `key` in the registered functions
#
# Comment keys:
#   * = This key is required to be manually set
#   + = This is an optional key under a required section
#   S = Script level section
#
# Usage: --config [this file].yml --inherit default(<-[Sect])+\
"""
}

# Stores the keys of a definitions file to allow easy changes
DK = NullDict({
    'ldesc'   : '.desc'    , # Long description
    'sdesc'   : '.short'   , # Short description
    'type'    : '.type'    ,
    'checks'  : '.checks'  ,
    'apply'   : '.apply'   ,
    'default' : '.default' ,
    'required': '.required',
    'number'  : '.number'  ,
    'children': '.children',
    'scripts' : '.scripts'
})


def format_defs(defs, level='', reqd=False):
    """
    Generates a list of tuples detailing how to write a default YAML using a
    requirements template.

    Parameters
    ----------
    defs: milkylib.Sect
        A MilkyLib requirements template

    level: str, default=''

    reqd: bool, default=False


    Returns
    -------
    write: list
        See notes.
    flags: list
        Additional information about each line that assists with YAML generation.
        Currently each entry is of the form (indent level, DK.scripts)

    Notes
    -----
    The `write` list contains tuples of strings. The strings in each tuple make up one
    line to be written to a YAML file. Each tuple consists of:
        (padded key: value, flag, type, description)
    where
        padded key  = yaml 'key: value' left padded for correct indentation
        flag        = Requirements flag:
                        ' ' = Optional, may be removed from the config
                        '*' = Required, must be set by the user
                        '+' = Optional key in a required Sect
        type        = The required type for the key, eg. int, str, bool
        description = Description of the key

    Using this the MilkyLib.utils.printTable can format these tuples of four strings
    into strings of four aligned columns. For example:

    >>> defs  =
    >>> write = format_v3(defs)
    >>> write
    [('Default', '?', 'Type', 'Description'),
     ('  key1: 0', ' ', 'int', '...'),
     ('  Sect:', '*', 'dict', '...'),
     ('    key2: f', '+', 'str', '...')]
    >>> printTable(write, columns={0: {'delimiter': '#', 'offset': 4},
    ...                            1: {'delimiter': '|', 'offset': 1}})
    Default        # ? | Type | Description
      key1: 0      #   | int  | ...
      Sect:        # * | dict | ...
        key2: f    # + | str  | ...
    """
    if len(defs) == 1 and DK.children in defs:
        return format_defs(defs[DK.children])

    lines  = []
    flags  = []
    level += '  '
    for key, rules in defs.items():

        # First prepare the comment for this key
        comment = [' ']
        if rules[DK.required]:
            comment = ['*']
        elif reqd:
            comment = ['+']

        type = rules.get(DK.type, '')
        if isinstance(type, list):
            type = ', '.join(type)

        comment.append(type)
        comment.append(rules.get(DK.ldesc, ''))

        info = {
            'level': len(level)/2,
            'scripts': rules.get(DK.scripts, 'all')
        }
        if DK.children in rules:
            lines.append((f'{level}{key}:', *comment))
            flags.append(info)

            if DK.type == 'list':
                level += '  '
                lines.append((f'{level}-', *Comments['list Sect']))
                flags.append(info)


            _write, _flags = format_defs(rules[DK.children], level, rules[DK.required])
            lines += _write
            flags += _flags
        else:
            if rules[DK.required]:
                value = rules.get(DK.default, rules[DK.type])
            else:
                value = rules.get(DK.default, '${!null}')

            if value is None:
                value = 'null'

            lines.append((f'{level}{key}: {value}', *comment))
            flags.append(info)

    return lines, flags


def full(lines, flags, Sects):
    """
    Generates a full template
    """
    default = ['all', None, []]
    # Discover which scripts each line belongs to.
    # If a parent is set to "all" and a child is not, the parent and all children will be
    # set to all scripts except for the non-"all" children. This allows for generating
    # multiple Sects with the same arguments
    for i, parent in enumerate(flags[:-1]):
        split = False
        for child in flags[i+1:]:
            # If they are the same or greater level then they are not parent/child
            if parent['level'] >= child['level']:
                break

            # Check if the child splits from the parent, ie. the child is unique to a script and the parent isn't
            if parent['scripts'] != child['scripts']:
                split = True
                break

        # Set all children with default scripts to be that of the parent
        if split:
            parent['scripts'] = Sects
            for child in flags[i+1:]:
                # Child is not actually a child of this parent
                if parent['level'] >= child['level']:
                    break

                # Otherwise set these scripts the same as the parent
                if child['scripts'] in default:
                    child['scripts'] = Sects

    Sects = {'default': [Comments['default']]} | {
        Sect: [
            (f'{Sect}:', 'S', 'Type', f'Options specific to the {Sect} script')
        ] for Sect in Sects
    }

    for i, line in enumerate(lines):
        if flags[i]['scripts'] in default:
            Sects['default'].append(line)
        else:
            for script in flags[i]['scripts']:
                Sects[script].append(line)

    instructions = []
    for Sect, lines in Sects.items():
        instructions.append(('', )) # Empty line between Sects
        instructions += lines

    return instructions


def generate(defs=None, style='full', comments='inline', file=None):
    """
    Generates a template YAML using a definitions document.

    Parameters
    ----------
    defs: mlky.Sect, default=None
        The requirements Sect object
    style: str, default='full'
        Style to generate the output as. Current methods:
        - full    = Top-level Sects contain all of the arguments that that
                    specific script uses
        - reduced = Top-level Sects contain only the script-specific arguments,
                    any 'all' arguments are placed in the default Sect
        - minimal = Only the required arguments are included
    comments: str, default='inline'
        Style to write the comments for each option. Current styles:
        - inline  = Comments are on the same line as the option
        - coupled = Comments are on the line above the option at the same level
        - None    = Comments are removed
    file: str, default=None
        File to write the generated YAML to

    Returns
    -------
    lines: list
        List of strings per line for the YAML template
    """
    if isinstance(defs, str):
        defs = Sect(name='defs', data=load_string(defs))

    lines, flags = format_defs(defs)

    # Discover the unique set of top-level Sects/scripts
    Sects = []
    for _, scripts in flags:
        if isinstance(scripts, list):
            Sects += scripts

    Sects = set(Sects)

    if style == 'full':
        instructions = full(lines, flags, Sects)
    elif style == 'reduced':
        instructions = reduced(lines, flags, Sects)
    elif style == 'minimal':
        instructions = minimal(lines, flags, Sects)
    else:
        Logger.error('Invalid style choice: {style!r}')
        return []

    lines = [Comments['header']]
    if comments == 'inline':
        lines += printTable(instructions,
            print   = None,
            columns = {
                0: {'delimiter': '#', 'offset': 8},
                1: {'delimiter': '|', 'offset': 1}
            }
        )

    elif comments == 'coupled':
        for line in instructions:
            if len(line) > 1:
                offset = len(line[0]) - len(line[0].lstrip())
                fmt,   = printTable([line[1:]], delimiter='|', prepend=' ' * offset + '# ', print=None)
                lines.append(fmt)
            lines.append(line[0])

    elif comments in [None, 'none']:
        lines += [line[0] for line in instructions]

    else:
        Logger.error('Invalid comments choice: {comments!r} - returning instructions')
        return instructions

    if file:
        with open(file, 'w') as out:
            out.write('\n'.join(lines))

    return lines
