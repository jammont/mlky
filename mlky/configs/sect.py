"""
The core of mlky: The Sect class.

This class acts like a fault-tolerant dict with dot notational syntax.
"""
import copy
import json
import logging
import os

from pathlib import Path

import yaml

from . import (
    Functions,
    Null,
    NullDict,
    NullType,
    Var
)
from ..utils import printTable
from ..utils.templates import yamlHeader


Logger = logging.getLogger(__file__)


class Sect:
    # Default values for when a subclass isn't fully initialized
    _name = ""
    _sect = NullDict()
    _dbug = -1
    _prnt = Null
    _type = 'Dict'

    # Class defaults, change these manually via Sect.__dict__[key] = ...
    _repr = 10 # __repr__ limiter to prevent prints being obnoxious

    def __init__(self,
        data    = {},
        name    = "",
        defs    = {},
        missing = False,
        debug   = -1,
        parent  = Null,
        **kwargs
    ):
        """
        Parameters
        ----------
        debug: int or list, defaults=-1
            Controls the verbosity of the class. Higher values is increased
            verbosity. Current levels:
                -1: Default, disables debug messages
                 0: Non-private functions (non-underscore named functions)
                 1: Private functions (single underscores)
                 2: _setdata()
                 3: getattr, get(), items()
                 4: Repr, very spammy
            If passed as a list of ints, will only enable those levels.
            If the list is comprised of strings, any function names in this list
            will be enabled

        Notes
        -----
        Initialization support:
        - From Sect     = Sect(Sect({...}))
        - From dict     = Sect({'a': 1, 'b': 2})
        - From list     = Sect(['a', 'b'])
        - From tuple    = Sect(('a', 'b'))
        - As a function = Sect(a=1, b=2)
        """
        if isinstance(debug, int):
            debug = range(0, debug+1)

        # Parse the input data from a supported type
        data = self.loadDict(data)

        self.__dict__['_name'] = name
        self.__dict__['_data'] = data
        self.__dict__['_miss'] = missing
        self.__dict__['_dbug'] = set(debug)
        self.__dict__['_prnt'] = parent
        self.__dict__['_sect'] = NullDict()

        if isinstance(data, dict):
            # if the input data is a dict, combine with kwargs to allow mix inputs eg. Sect({'a': 1}, b=2)
            for key, value in (kwargs | data).items():
                defs = defs.get(f'.{key}', {})
                self._setdata(key, value, defs=defs)

        elif isinstance(data, (list, tuple)):
            # Flag that this is a list-type Sect to change some downstream behaviours
            self.__dict__['_type'] = 'List'
            for i, value in enumerate(data):
                self._setdata(i, value, defs=defs)

        elif isinstance(data, Sect):
            super().__setattr__('__dict__', data.deepCopy().__dict__)

        if defs:
            self.applyDefinition(defs)

    def __call__(self, other, inplace=True):
        """
        Enables patching via call, Sect(other)
        """
        if isinstance(other, (type(self), dict)):
            return self._patch(other, inplace=inplace)
        raise TypeError(f'mlky.Sect can only be patched using other dicts or Sects')

    def __eq__(self, other):
        if self._dbug:
            self._log(1, '__eq__', f'Comparing to type: {type(other)} = {other!r}')

        # Convert this to its primitive type for safer comparisons
        data = self.toPrimitive()

        # Same if compared to another Sect
        if isinstance(other, (type(self), Sect)):
            other = other.toPrimitive()

        return data == other

    def __or__(self, other):
        """
        Enables patching using the | operator

        Notes
        -----
        To enable subclass patching behaviour with both itself and this class,
        check if isinstance of itself and Sect
        """
        if isinstance(other, (type(self), Sect, dict)):
            return self._patch(other, inplace=False)
        raise TypeError(f'mlky.Sect can only use operator | (or) with other dicts or Sects')

    def __lt__(self, other):
        """
        Enables patching using the < operator

        Notes
        -----
        To enable subclass patching behaviour with both itself and this class,
        check if isinstance of itself and Sect
        """
        if isinstance(other, (type(self), Sect, dict)):
            return self._patch(other, inplace=False)
        raise TypeError(f'mlky.Sect can only use operator < (lt) with other dicts or Sects')

    def __setattr__(self, key, value):
        self._setdata(key, value)

    def __setitem__(self, key, value):
        self._setdata(key, value)

    def __getattr__(self, key, var=False, default=True):
        """
        Interfaces with _sect to retrieve the Var and Sect child objects
        _sect should always be a NullDict

        Parameters are accessible via the .get() method

        Parameters
        ----------
        key: str
            Attribute name to look up
        var: bool, defaults=False
            Return the item as a Var
        default: bool, defaults=True
            Return a Var's default value if available
        """
        val = self._sect[key]

        if isinstance(val, Var):
            if var:
                self._log(3, '__getattr__', f'[{key!r}] Returning as Var: {val}')
                return val

            if default and val.value is Null:
                self._log(3, '__getattr__', f'[{key!r}] Returning {val}.default')
                return val.default

            self._log(3, '__getattr__', f'[{key!r}] Returning {val}.value')
            return val.value

        if not isinstance(val, (Sect, NullType)):
            self._log('e', '__getattr__', f'Item of _sect is not a Var, Sect, or Null type: [{key!r}] = {type(val)} {val}')

        self._log(3, '__getattr__', f'[{key!r}] Returning value: {val!r}')
        return val

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __contains__(self, key):
        return key in self._sect

    def __iter__(self):
        return iter(self._sect)

    def __len__(self):
        return len(self._sect)

    def __reduce__(self):
        # TODO: Update
        return (type(self), (
            self.toPrimitive(), self._name, self._defs,
            self._miss
        ))

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        for key, val in self.__dict__.items():
            self._log(1, '__deepcopy__', f'Deep copying __dict__[{key!r}] = {val!r}')
            new.__dict__[key] = copy.deepcopy(val, memo)
        return new

    def __delattr__(self, key):
        self._log(2, '__delattr__', f'Deleting self._sect[{key!r}]')
        del self._sect[key]

    def __delitem__(self, key):
        delattr(self, key)

    def __repr__(self):
        """
        """
        attrs, sects = [], []
        for key, value in self.items():
            self._log(4, '__repr__', f'Checking key [{key!r}] {type(value)} {value!r}')
            if isinstance(value, Sect):
                sects.append(key)
                self._log(4, '__repr__', '└ This key is a Sect')
            else:
                attrs.append(key)
                self._log(4, '__repr__', '└ This key is an Attr')

        # Shorten the length of these strings if there's too many keys
        if len(attrs) > self._repr:
            attrs = f'{attrs[:self._repr]}+[{len(attrs)-self._repr} more]'
        if len(sects) > self._repr:
            sects = f'{sects[:self._repr]}+[{len(sects)-self._repr} more]'

        # TODO: Expanded formatted repr?
        return f"<{type(self).__name__} {self._name or '.'} (Attrs={attrs}, Sects={sects})>"

    @property
    def _offset(self):
        """
        Offset in spaces to denote hierarchical level
        """
        return '  ' * (len(self._name.split('.')) - 1)

    def _log(self, level, func, msg):
        """
        Formats debug messages
        """
        message = f'{self._offset}<{type(self).__name__}>({self._name}).{func}() {msg}'
        if level == 'e':
            Logger.error(message)
        elif level in self._dbug or func in self._dbug:
            Logger.debug(message)

    def _patch(self, other, inplace=True):
        """
        Patches this Sect using another Sect or dict
        """
        if not inplace:
            self = self.deepCopy()
            self._log(1, '_patch', 'Patching on deep copy')

        # Auto cast to Sect so merges are easier
        for key, item in Sect(other).items(var=True):
            name = self._subkey(key)
            data = self.get(key, var=True)

            if isinstance(item, Sect):
                # Patch two Sects together
                if isinstance(data, Sect):
                    self._log(1, '_patch', f'Patching sub Sect [{key!r}] = {data} | {item}')
                    self[key] = data | item
                # Replace with the other Sect
                else:
                    self._log(1, '_patch', f'Adding sub Sect [{key!r}] = {item}')
                    self[key] = item
            else:
                # Log whether this is replacing or adding a Var, or if something borked
                if isinstance(item, Var):
                    if isinstance(data, Var):
                        self._log(1, '_patch', f'Replacing Var [{key!r}] = {item!r}')
                    else:
                        self._log(1, '_patch', f'Adding Var [{key!r}] = {item!r}')
                else:
                    self._log('e', '_patch', f'A value other than a Sect or Var was found and should not have been: {type(item)} = {item!r}')

                self[key] = item

        # Update the name to reflect potential changes in the hierarchy
        # self.updateNames()

        return self

    def _subkey(self, key):
        """
        Formats a key into a subkey name for this Sect
        """
        if isinstance(key, int):
            return f'{self._name}[{key}]'
        return f'{self._name}.{key}'

    def _setdata(self, key, value, defs={}, **kwargs):
        """
        Sets an item/attribute into the Sect
        """
        # Generate the proper name for this key
        name = self._subkey(key)

        # Retrieve this key from self if it exists
        self._log(2, '_setdata', f'Retrieving if this key [{key!r}] already exists')
        data = self.get(key, var=True)

        # Already a Var object, typically from unpickling
        if isinstance(value, Var):
            self._log(2, '_setdata', f'Input was a Var, setting self[{key!r}] = {value}')
            self._sect[key] = value
            value._update(key, self)

        # Already a Sect, typically from patching
        elif isinstance(value, (type(self), Sect)):
            self._log(2, '_setdata', f'Input was a Sect, setting self[{key!r}] = {value}')
            self._sect[key] = value
            value._update(key, self)

        # These types are Sects, everything else will be Vars
        elif isinstance(value, (dict, list, tuple)):
            self._log(2, '_setdata', f'Setting new Sect [{key!r}] = Sect({value}, defs={defs})')
            self._sect[key] = Sect(
                name   = name,
                data   = value,
                defs   = defs,
                debug  = self._dbug,
                parent = self,
                **kwargs
            )

        # Key already exists, Var object instantiated
        elif isinstance(data, Var):
            # The Var obj will report any issues with setting the value (eg. failed checks)
            self._log(2, '_setdata', f'Updating existing Var [{key!r}]: {data}.value = {value}')
            data.value = value

        # Create as a Var object
        else:
            self._log(2, '_setdata', f'Setting new Var [{key!r}] = Var({value}, kwargs={kwargs}))')
            self._sect[key] = Var(
                name   = name,
                key    = key,
                value  = value,
                debug  = self._dbug,
                parent = self,
                **kwargs
            )

        # Always apply at the end if there's new defs, no harm if not
        self._log(2, '_setdata', f'[{key!r}] Applying defs: {defs}')
        self.get(key, var=True).applyDefinition(defs)

    def _setdefs(self, key, defs):
        """
        Sets keys from a definitions dictionary
        """
        value = Null

        # Children start with '.'
        if any(key.startswith('.') for key in defs):
            value = {}
            if defs.get('dtype') == 'list':
                value = [{} for _ in range(defs.get('repeat', 1))]

        self._setdata(key, value, defs=defs, missing=True)

    def _update(self, key, parent=Null):
        """
        Updates parameters of self relative to parent, then updates its children

        Parameters
        ----------
        key: str
            The key the parent is using for this child
        parent: mlky.Sect, defaults=mlky.Null
            The parent of this child
        """
        # Update self
        internal = self.__dict__
        internal['_prnt'] = parent
        internal['_dbug'] = parent._dbug

        # Log important changes
        old = internal['_name']
        new = parent._subkey(key)
        if new is not Null and new != old:
            self._log(1, '_update', f'Updating name from {old!r} to {new}')
            internal['_name'] = new

        # Update children
        self.deepUpdate()

    def applyDefinition(self, defs):
        """
        Applies a definitions object against this Sect
        """
        self.__dict__['_defs'] = defs = self.loadDict(defs)

        # Apply definitions to child keys, or create the key if missing
        for key, val in defs.items():
            if key.startswith('.'):
                key = key[1:]
                if key not in self:
                    self._log(0, 'applyDefinition', f'Adding missing key {key!r}')
                    self._setdefs(key, val)
                else:
                    self._log(0, 'applyDefinition', f'Applying defs to key {key!r}')
                    self.get(key, var=True).applyDefinition(val)

    def deepUpdate(self):
        """
        Calls _update() on each Var/Sect in self. This will bring parent/child
        relationships in line with the current data, such as names and keys
        """
        for key, item in self.items(var=True):
            if not isinstance(item, (type(self), Sect, Var)):
                self._log('e', 'deepUpdate', f'Should never encounter any type other Sect or Var, got: {type(item)} = {item}')
            item._update(key, self)

    def deepCopy(self, memo=None):
        """
        Deep copies this Sect

        Parameters
        ----------
        memo: dict, defaults=None
            Deep copy memo to pass. See notes for further detail

        Returns
        -------
        type(self)
            Deep copy of this object

        Notes
        -----
        The purpose of the `memo` is to track already once-copied objects in
        case they are copied again to return faster. Because these are intended
        to be highly mutable objects, that optimization tends to cause more
        problems than it's worth. This is disabled by setting `memo` to `None`.
        However, if you would like to leverage a memo, instantiate a dict
        variable and pass it as the memo, such as:
        ```
        >>> sect = Sect({'a': 1})
        >>> memo = {}
        >>> copy = sect.deepCopy(memo)
        >>> memo
        {4428805649: <Sect . (Attrs=['a'], Sects=[])>,
         4432035072: {'a': 1},
         4433694400: [{'a': 1},
          {},
          [],
          set(),
          {'a': <Var(a=1)>},
          <Sect . (Attrs=['a'], Sects=[])>],
         4429609728: {},
         4433587008: [],
         4428133120: set(),
         4428632752: {'a': <Var(a=1)>},
         4428805648: <Sect . (Attrs=['a'], Sects=[])>}
        ```
        This memo now acts a snapshot of the current state of the object. If you
        want to recreate this snapshot, call `sect.deepCopy(memo)` again.
        """
        self._log(0, 'deepCopy', f'Creating deep copy using memo: {memo}')
        return copy.deepcopy(self, memo)

    def get(self, key, other=None, var=False, default=True):
        """
        Parameters
        ----------
        key: str
            Item name to look up
        other: any, defaults=None
            If
        var: bool, defaults=False
            Return the item as a Var
        default: bool, defaults=True
            If a default value is available, return that instead of `other`
        """
        val = self.__getattr__(key, var=var, default=default)

        if val is Null:
            self._log(3, 'get', f'[{key!r}] Val is Null, returning other: {other!r}')
            return other

        self._log(3, 'get', f'[{key!r}] Returning value: {val!r}')
        return val

    def keys(self):
        return self._sect.keys()

    def values(self, var=False):
        self._log(3, 'values', f'Returning values with var={var}')
        return [self.get(key, var=var) for key in self]

    def items(self, var=False):
        """
        """
        self._log(3, 'items', f'Returning items with var={var}')
        return [(key, self.get(key, var=var)) for key in self]

    def hasAttrs(self):
        """
        Returns whether this Sect has child attributes
        """
        for key, value in self.items():
            if isinstance(value, Var):
                return True
        return False

    def hasSects(self):
        """
        Returns whether this Sect has child Sects
        """
        for key, value in self.items():
            if isinstance(value, Sect):
                return True
        return False

    def toDict(self, deep=True, var=False):
        """
        Converts the Sect to a dict object

        Parameters
        ----------
        deep: bool, defaults=True
            Will convert child Sects to primitive types as well
        var: bool, defaults=False
            Returns the Var object instead of its value
        """
        data = {}
        for key, item in self._sect.items():
            value = self[key]
            if var:
                data[key] = item
            elif deep and isinstance(item, Sect):
                self._log(0, 'toDict', f'Converting child Sect [{key!r}].toPrimitive()')
                data[key] = value.toPrimitive(var=var)
            else:
                data[key] = value

        return data

    def toList(self, deep=True, var=False):
        """
        Converts the sect to a list object

        Parameters
        ----------
        deep: bool, defaults=True
            Will convert child Sects to primitive types as well
        var: bool, defaults=False
            Returns the Var object instead of its value
        """
        data = []
        for key, item in self._sect.items():
            value = self[key]
            if var:
                data.append(item)
            elif deep and isinstance(item, Sect):
                self._log(0, 'toList', f'Converting child Sect [{key!r}].toPrimitive()')
                data.append(value.toPrimitive(var=var))
            else:
                data.append(value)

        return data

    def toPrimitive(self, *args, **kwargs):
        """
        Determines what type of primitive type to convert this Sect to

        Current types:
            dict
            list
        """
        return getattr(self, f'to{self._type}')(*args, **kwargs)

    def resetVars(self):
        """
        Runs reset on each Var
        """
        for key, item in self._sect.items():
            if isinstance(item, Sect):
                item.resetVars()
            elif isinstance(item, Var):
                item.reset()
            else:
                self._log('e', 'resetVars', f'Internal _sect has a value other than a Var or Sect: {key!r} = {item!r}')

    def dumpYaml(self, string=True):
        """
        Dumps this object as a YAML string.

        Leverages the yaml.dump function to ensure 'key: value' are yaml
        compatible

        Parameters
        ----------
        string: bool, default=True
            Converts the dump to a compatible YAML string. If false, returns
            the dump list which is a list of tuples where each tuple defines the
            column values for a given row

        Notes
        -----
        `string=False` will return the `dump` list. The `dump` list is a list
        of tuples, ie.
        ```
        dump = [
            (string, flag, dtype, sdesc), # Line 1
            (string, flag, dtype, sdesc), # Line 2
            ...
        ]
        ```
        This list is in order. If the order changes, it risks becoming an
        invalid YAML. This list is formatted as such so that it can be easily
        passed to `mlky.utils.printTable()`. See `Sect.generateTemplate()` for
        more information about this.
        """
        def rowFromSect(string, sect):
            """
            Reads a Sect and prepares a tuple that represents the row as the
            following columns:
                (string, flag, dtype, sdesc)
            """
            defs = sect._defs

            sdesc = defs.get('sdesc', '')
            dtype = defs.get('dtype', 'dict')

            # ! = required, ? = optional under a required sect, ' ' = optional
            flag = ' '
            if defs.get('required'):
                flag = '!'
            else:
                parent = sect._prnt
                while parent is not Null:
                    if parent._defs.get('required'):
                        flag = '?'
                        break
                    parent = parent._prnt

            return (string, flag, dtype, sdesc)


        def rowFromVar(var):
            """
            Reads a Var and prepares a tuple that represents the row as the
            following columns:
                (string, flag, dtype, sdesc)
            where:
                `string` is the "key: value" for this line
                `flag` is one of:
                    ` ` - Completely optional key
                    `!` - Manually set value required
                    `?` - Optional child key of some required parent section
                `dtype` is the set data type for this key
                `sdesc` is the short description

            This list of tuples is then processed by utils.printTable() to the
            columns in alignment as a valid yaml
            """
            # Set value if set, otherwise use default, replace Null with `\`
            value  = '\\'
            if var.value is not Null:
                value = var.value
            elif var.default is not Null:
                value = var.default

            flag = ' '
            if var.required:
                flag = '!'
            else:
                parent = var.parent
                while parent is not Null:
                    if parent._defs.get('required'):
                        flag = '?'
                        break
                    parent = parent._prnt

            # Use yaml to dump this correctly
            strings = yaml.dump({key: value}).split('\n')[:-1]

            # If this is a list value, there will be multiple lines
            others = []
            if len(strings) > 1:
                offset = var._offset + '  '
                others = [
                    (offset+string, )
                    for string in strings[1:]
                ]

            # The main key line
            string = var._offset + strings[0]

            return [(string, flag, var.dtype or '', var.sdesc)] + others


        dump = [('generated:', 'K', 'dtype', 'Short description')]
        for key, item in self.items(var=True):
            if isinstance(item, Sect):
                # `key` is not in the item, create the "key: value" string for the row tuple
                dump.append(rowFromSect(f'{item._offset}{key}:', item))
                dump += item.dumpYaml(string=False)[1:]
            elif isinstance(item, Var):
                dump += rowFromVar(item)
            else:
                self._log('e', 'dumpYaml', f'Internal _sect has a value other than a Var or Sect: {key!r} = {item!r}')

        if string:
            return '\n'.join(
                printTable(dump, columns = {
                        0: {'delimiter': '#'},
                        1: {'delimiter': '|'},
                    }, print=None
                )
            )
        return dump

    def generateTemplate(self, file=None):
        """
        Generates a YAML template file
        """
        dump = yamlHeader + self.dumpYaml(string=True)

        if file:
            with open(file, 'w') as f:
                f.write(dump)

    def loadDict(self, data):
        """
        Loads a dict from various options:
            - Files:
                - .json
                - .yaml, .yml
            - Strings:
                - yaml formatted
                - pathlib.Path
            - Returns these types as-is:
                - type(self)
                - Sect
                - dict
                - list
                - tuple

        Parameters
        ----------
        data: varies
            One of the various supported types in the function description

        Returns
        -------
        """
        # Dicts and Sects return as-is
        dtypes = [type(self), Sect, dict, list, tuple]
        if isinstance(data, tuple(dtypes)):
            return data

        dtypes += ['yaml', 'json', 'pathlib.Path']
        if isinstance(data, (str, Path)):
            # File case
            if os.path.isfile(data):
                _, ext = os.path.splitext(data)

                if ext in ['.yml', '.yaml']:
                    with open(data, 'r') as file:
                        data = yaml.load(file, Loader=yaml.FullLoader)
                elif ext in ['.json']:
                    return json.loads(data)

            else:
                try:
                    # Raw yaml strings supported only
                    data = yaml.load(data, Loader=yaml.FullLoader)
                except:
                    raise TypeError('Data input is a string but is not a file nor a yaml string')

            return data

        else:
            raise TypeError(f'Data input is not a supported type, got {type(data)!r} expected one of: {dtypes}')
