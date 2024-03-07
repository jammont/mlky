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
    ErrorsDict,
    funcs,
    Null,
    NullDict,
    NullType,
    Var
)
from ..utils import printTable
from ..utils.templates import yamlHeader


Logger = logging.getLogger(__file__)


def reportErrors(errors, offset=''):
    """
    Pretty prints an errors dictionary to logging.error
    """
    for key, errs in errors.items():
        if key.startswith('.'):
            name = key.split('.')[-1]
            Logger.error(offset + f'.{name}')
            reportErrors(errs, offset+'  ')
        else:
            if isinstance(errs, list):
                for err in errs:
                    Logger.error(offset + f'- {key}: {err}')
            else:
                Logger.error(offset + f'- {key}: {errs}')


class Sect:
    # Default values for when a subclass isn't fully initialized
    _name = ""
    _sect = NullDict()
    _defs = {}
    _dbug = -1
    _prnt = Null
    _type = 'Dict'
    _chks = []

    # Options to control the behaviour of the Sect object for all Sect objects
    _opts = NullDict(
        # TODO: (Doc this better) Not converting list types will prevent the ability to patch them, values for these keys will simply be replaced on patch
        convertListTypes = True,
        convertItems     = True,
        VarsReplaceInit  = True,
        Var              = Var # Passthrough to access Var options via this dict
    )

    # Class defaults, change these manually via Sect.__dict__[key] = ...
    _repr = 10 # __repr__ limiter to prevent prints being obnoxious

    def __init__(self,
        data    = {},
        name    = "",
        defs    = {},
        missing = False,
        debug   = -1,
        parent  = Null,
        _opts   = {},
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
        _opts: dict, defaults={}
            Override options for this Sect and its children only. This will also detach
            this Sect from the global options, so those changes will not propogate

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

        # Override the options for this Sect if given
        if _opts:
            self.__dict__['_opts'] = NullDict(self._opts | _opts)

        # Parse the input data from a supported type
        data = self.loadDict(data)
        defs = self.loadDict(defs)

        self.__dict__['_name'] = name
        self.__dict__['_data'] = data
        self.__dict__['_miss'] = missing
        self.__dict__['_dbug'] = set(debug)
        self.__dict__['_prnt'] = parent
        self.__dict__['_chks'] = []
        self.__dict__['_sect'] = NullDict()
        self.__dict__['_defs'] = {}

        if isinstance(data, dict):
            # if the input data is a dict, combine with kwargs to allow mix inputs eg. Sect({'a': 1}, b=2)
            for key, value in (kwargs | data).items():
                self._setdata(key, value)

        elif isinstance(data, (list, tuple)):
            # Flag that this is a list-type Sect to change some downstream behaviours
            self.__dict__['_type'] = 'List'
            for i, value in enumerate(data):
                self._setdata(i, value)

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
    def _f(self):
        """
        A 'flags' function to standardize internal attribute lookups between
        Sect and Var objects.

        While Vars just use plain words for attributes such as `Var.checks`,
        Sects use an underscore followed by a standard 4 letters like
        `Sect._chks`. This property on both classes will access the same desired
        attribute:
            Var.checks == Var._f.checks <=> Sect._f.checks == Sect._chks

        Which is useful when iterating over a list that may contain both Var
        and Sect objects:
        ```
        >>> Config({'a': 1, 'b': {}})
        >>> for key, item in Config.items(var=True):
        ...     print(key, type(item), item._f.name)
        a <class 'mlky.configs.var.Var'> .a
        b <class 'mlky.configs.sect.Sect'> .b
        ```
        One caveat: on Var objects this works fine, but on Sect objects this
        is read-only due to creating a view of internal attributes rather than
        be the attribute variables themselves
        """
        return NullDict(
            name    = self._name,
            value   = self._sect,
            dtype   = self._type,
            defs    = self._defs,
            checks  = self._chks,
            debug   = self._debug,
            parent  = self._prnt,
            update  = self._update,
            missing = self._miss,
        )

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

        Notes
        -----
        * Not converting ListTypes (list, tuple) to Sect limits a few capabilities:
            - These types become Vars, so patching doesn't work. Patching two Sects
            together will write one Var list over the other
            - In order for resetVars to work, _opts.VarsReplaceInit will be set to
            `False` for all child Sects of this list, if _opts.convertItems is `True`
            This will result in any new Vars created on these Sects will not auto call
            replace.
        """
        # Generate the proper name for this key
        name = self._subkey(key)

        # Retrieve this key from self if it exists
        self._log(2, '_setdata', f'Retrieving if this key [{key!r}] already exists')
        data = self._sect[key]

        # Var is the last resort type
        setVar = False

        # Reduce duplicate code as this is repeated a few times
        args = dict(
            name   = name,
            data   = value,
            # defs   = defs,
            debug  = self._dbug,
            parent = self
        )

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
        elif isinstance(value, dict):
            self._log(2, '_setdata', f'Setting new Sect [{key!r}] = Sect({value}, defs={defs})')
            self._sect[key] = Sect(**args, **kwargs)

        # List types may be Sects, depends on options set
        elif isinstance(value, (list, tuple)):
            # if convertListTypes then we set a Sect, all other option combinations create a Var
            setVar = True

            # Default behaviour, cast to a Sect
            if self._opts.convertListTypes:
                self._log(2, '_setdata', f'Setting new Sect [{key!r}] = Sect({value}, defs={defs})')
                self._sect[key] = Sect(**args, **kwargs)
                setVar = False

            # If not, should the items of the list be converted?
            elif self._opts.convertItems:
                self._log(2, '_setdata', f'Setting new List [{key!r}] as Var')
                opts  = dict(convertListTypes=True, VarsReplaceInit=False)
                value = Sect(_opts=opts, **args, **kwargs).toPrimitive(deep=False)

        # Key already exists, Var object instantiated
        elif isinstance(data, Var):
            # The Var obj will report any issues with setting the value (eg. failed checks)
            self._log(2, '_setdata', f'Updating existing Var [{key!r}]: {data}.value = {value}')
            data.value = value

        else:
            # All other cases will create a new Var
            setVar = True

        # Create as a Var object
        if setVar:
            self._log(2, '_setdata', f'Setting new Var [{key!r}] = Var({value}, kwargs={kwargs}))')
            self._sect[key] = Var(
                name    = name,
                key     = key,
                value   = value,
                debug   = self._dbug,
                parent  = self,
                replace = self._opts.VarsReplaceInit,
                **kwargs
            )

        # Update definitions at the end regardless of input type
        if defs:
            self._log(2, '_setdata', f'[{key!r}] Applying defs: {defs}')
            self._sect[key].applyDefinition(defs)

    def _setdefs(self, key, defs):
        """
        Sets keys from a definitions dictionary
        """
        value = Null
        dtype = defs.get('dtype')

        if dtype == 'list':
            self.__dict__['_type'] = 'List'
            copies  = range(defs.get('repeat', 0))
            subdefs = defs.get('items', defs)
            subval  = Null
            if any(key.startswith('.') for key in subdefs):
                subval = {}
            value = [subval for _ in copies]

        elif dtype == 'dict':
            copies = defs.get('repeat', [])
            value  = {key: {} for key in copies}
        elif any(key.startswith('.') for key in defs):
            value = {}

        self._log(1, '_setdefs', f'[{key!r}] = {value!r}, defs={defs}')
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
        defs = self.loadDict(defs)
        self.__dict__['_defs'] = defs

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
            elif key == 'items':
                for name, child in self.items(var=True):
                    self._log(0, 'applyDefinition', f'Applying defs to child {key!r}')
                    child.applyDefinition(val)

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

    def values(self, *args, **kwargs):
        self._log(3, 'values', f'args={args}, kwargs={kwargs}')
        return [self.__getattr__(key, *args, **kwargs) for key in self]

    def items(self, *args, **kwargs):
        """
        """
        self._log(3, 'items', f'args={args}, kwargs={kwargs}')
        return [(key, self.__getattr__(key, *args, **kwargs)) for key in self]

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

    def dumpYaml(self, key=Null, string=True, truncate=None):
        """
        Dumps this object as a YAML string.

        Leverages the yaml.dump function to ensure 'key: value' are yaml compatible

        Parameters
        ----------
        string: bool, default=True
            Converts the dump to a compatible YAML string. If false, returns
            the dump list which is a list of tuples where each tuple defines the
            column values for a given row
        truncate: int, default=None
            `truncate` argument of mlky.utils.printTable; only relevant if
            `string=True`

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
        defs  = self._defs
        sdesc = defs.get('sdesc', '')
        dtype = defs.get('dtype', self._type.lower())

        # ! = required, ? = optional under a required sect, ' ' = optional
        flag = ' '
        if defs.get('required'):
            flag = '!'
        else:
            parent = self._prnt
            while parent is not Null:
                if parent._defs.get('required'):
                    flag = '?'
                    break
                parent = parent._prnt

        if key is None:
            key = self._f.name
        if key is Null:
            line = [['generated:', 'K', 'dtype', 'Short description']]
        else:
            if key == '':
                line = ''
            else:
                line = f'{key}:'
            line = [[line, flag, dtype, sdesc]]

        # Dump all child objects to yaml
        lines = []
        for name, child in self.items(var=True):
            lines += child.dumpYaml(name, string=False)

        # Apply offset
        if lines:
            for i, child in enumerate(lines):
                lines[i][0] = '  ' + child[0]

        dump = line + lines
        if string:
            return '\n'.join(
                printTable(dump, columns = {
                        0: {'delimiter': '#'},
                        1: {'delimiter': '|'},
                    },
                    print    = None,
                    truncate = truncate
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

    def validate(self, report=True, asbool=True):
        """
        Validates a Sect and its children

        Parameters
        ----------
        report: bool, default=True
            Reports the (reduced) errors to logger.error in a pretty format
        asbool: bool, default=True
            Returns the errors dict as an inverted boolean, True for no errors, False for errors

        Returns
        -------
        errors: dict
            Errors dictionary that contains all the checks for each key. This is a
            special dictionary that can be reduced using errors.reduce() to only see
            checks that failed validation
        """
        defs = self._defs

        # Find which children are assigned to each tag
        tags = {}
        for key in defs:
            if not key.startswith('.'):
                continue
            for tag in defs[key].get('tags', []):
                tags.setdefault(tag, []).append(key[1:])

        errors = ErrorsDict()

        # Now apply the check functions against the assigned tags
        for check in defs.get('checks', []):
            (check, args), = list(check.items())

            if isinstance(args, str):
                args = [args,]

            for tag in args:
                items = [self.get(key, var=True) for key in tags[tag]]

                errors[f'{check}[{tag}]'] = funcs.getRegister(check)(items)

        # Now validate children
        for child in self.values(var=True):
            name = child.name if isinstance(child, Var) else child._name
            errors[name] = child.validate(report=False, asbool=False)

        if report:
            reduced = errors.reduce()
            if reduced:
                Logger.error('Errors discovered in the configuration:')
                reportErrors(reduced, '  ')
            else:
                Logger.info('Configuration passed all checks')

        if asbool:
            return not bool(errors.reduce())
        return errors
