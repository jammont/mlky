"""
Sect objects maintain a dictionary of other Sect and Var objects
"""
import copy
import logging

import yaml

from . import (
    Functions,
    Null,
    Var
)


Logger = logging.getLogger(__file__)


class nict(dict):
    """
    Simple dict extension that enables dot notation and defaults to Null when an
    item/attribute is missing Null+dict=nict
    """
    def __deepcopy__(self, memo):
        new = type(self)(self)
        memo[id(self)] = new
        return new

    def __getattr__(self, key):
        return super().get(key, Null)

    def __getitem__(self, key):
        return self.__getattr__(key)

    def get(self, key, other=None, **kwargs):
        val = self[key]
        if val is not Null:
            return val
        return other


class Sect:
    # Default values for when a subclass isn't fully initialized
    _name = ""
    _sect = nict()
    _dbug = -1
    _prnt = Null

    # Class defaults, change these manually via Sect._key = ...
    _repr = 10 # __repr__ limiter to prevent prints being obnoxious

    def __init__(self, data={}, name="", defs={}, missing=False, debug=-1, parent=Null, **kwargs):
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

        self.__dict__['_name'] = name
        self.__dict__['_data'] = data
        self.__dict__['_defs'] = nict(defs)
        self.__dict__['_miss'] = missing
        self.__dict__['_dbug'] = set(debug)
        self.__dict__['_prnt'] = parent
        self.__dict__['_sect'] = nict()

        children = defs.get('.children', {})
        if isinstance(data, dict):
            # if the input data is a dict, combine with kwargs to allow mix inputs eg. Sect({'a': 1}, b=2)
            for key, value in (kwargs | data).items():
                self._setdata(key, value, defs=children.get(key, {}))

        elif isinstance(data, (list, tuple)):
            for i, value in enumerate(data):
                self._setdata(i, value, defs=defs)

        elif isinstance(data, Sect):
            super().__setattr__('__dict__', data.deepCopy().__dict__)

    def __call__(self, other, inplace=True):
        """
        Enables patching via call, Sect(other)
        """
        if isinstance(other, (type(self), dict)):
            return self._patch(other, inplace=inplace)
        raise TypeError(f'mlky.Sect can only be patched using other dicts or Sects')

    def __eq__(self, other):
        if self._dbug:
            Logger.debug(f'Comparing to {type(other)}: {other}')
        data = self.toDict()
        if isinstance(other, dict):
            return data == other
        elif isinstance(other, (type(self), Sect)):
            return data == other.toDict()
        return False

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

    def __getattr__(self, key):
        """
        """
        # _sect starts as a nict and sometimes turns into a Sect, .get accounts for both
        val = self._sect.get(key, other=Null, var=True)
        if isinstance(val, Var):
            self._debug(3, '__getattr__', f'Returning {val}.value')
            return val.value

        self._debug(3, '__getattr__', f'Returning value: {val!r}')
        return val

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __contains__(self, key):
        return key in self._sect

    def __iter__(self):
        return iter(self._sect)

    def __reduce__(self):
        # TODO: Update
        return (type(self), (
            self.toDict(), self._name, self._defs,
            self._miss
        ))

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        for key, val in self.__dict__.items():
            self._debug(1, '__deepcopy__', f'Deep copying __dict__[{key!r}] = {val!r}')
            new.__dict__[key] = copy.deepcopy(val, memo)
        return new

    def __delattr__(self, key):
        self._debug(2, '__delattr__', f'Deleting self._sect[{key!r}]')
        del self._sect[key]

    def __delitem__(self, key):
        delattr(self, key)

    def __repr__(self):
        """
        """
        attrs, sects = [], []
        for key, value in self.items():
            self._debug(4, '__repr__', f'Checking key [{key!r}] {type(value)} {value!r}')
            if isinstance(value, Sect):
                sects.append(key)
                self._debug(4, '__repr__', '└ This key is a Sect')
            else:
                attrs.append(key)
                self._debug(4, '__repr__', '└ This key is an Attr')

        if len(attrs) > self._repr:
            attrs = f'{attrs[:self._repr]}+[{len(attrs)-self._repr} more]'
        if len(sects) > self._repr:
            sects = f'{sects[:self._repr]}+[{len(sects)-self._repr} more]'

        return f"<{type(self).__name__} {self._name or '.'} (Attrs={attrs}, Sects={sects})>"

    @property
    def _offset(self):
        """
        Offset in spaces to denote hierarchical level
        """
        return '  ' * (len(self._name.split('.')) - 1)

    def _debug(self, level, func, msg):
        """
        Formats debug messages
        """
        if level in self._dbug or func in self._dbug:
            Logger.debug(f'{self._offset}<{type(self).__name__}>({self._name}).{func}() {msg}')

    def _patch(self, other, inplace=True):
        """
        Patches this Sect using another Sect or dict
        """
        if not inplace:
            self = self.deepCopy()
            self._debug(1, '_patch', 'Patching on deep copy')

        # Auto cast to Sect so merges are easier
        for key, item in Sect(other).items(var=True):
            name = self._subkey(key)
            data = self.get(key, var=True)

            if isinstance(item, Sect):
                # Patch two Sects together
                if isinstance(data, Sect):
                    self._debug(1, '_patch', f'Patching sub Sect [{key!r}] = {data} | {item}')
                    self[key] = data | item
                # Replace with the other Sect
                else:
                    self._debug(1, '_patch', f'Adding sub Sect [{key!r}] = {item}')
                    self[key] = item
            else:
                # Log whether this is replacing or adding a Var, or if something borked
                if isinstance(item, Var):
                    if isinstance(data, Var):
                        self._debug(1, '_patch', f'Replacing Var [{key!r}] = {item!r}')
                    else:
                        self._debug(1, '_patch', f'Adding Var [{key!r}] = {item!r}')
                else:
                    Logger.error(f'A value other than a Sect or Var was found and should not have been: {type(item)} = {item!r}')

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
        self._debug(2, '_setdata', f'Retrieving if this key [{key!r}] already exists')
        data = self.get(key, var=True)

        # Already a Var object, typically from unpickling
        if isinstance(value, Var):
            self._debug(2, '_setdata', f'Input was a Var, setting self[{key!r}] = {value}')
            self._sect[key] = value
            value._update(key, self)

        # Already a Sect, typically from patching
        elif isinstance(value, (type(self), Sect)):
            self._debug(2, '_setdata', f'Input was a Sect, setting self[{key!r}] = {value}')
            self._sect[key] = value
            value._update(key, self)

        # These types are Sects, everything else will be Vars
        elif isinstance(value, (dict, list, tuple)):
            self._debug(2, '_setdata', f'Setting new Sect [{key!r}] = Sect({value}, defs={defs})')
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
            self._debug(2, '_setdata', f'Updating existing Var [{key!r}]: {data}.value = {value}')
            data.value = value

        # Create as a Var object
        else:
            self._debug(2, '_setdata', f'Setting new Var [{key!r}] = Var({value}, defs={defs}, kwargs={kwargs}))')
            self._sect[key] = Var(
                name   = name,
                key    = key,
                value  = value,
                debug  = self._dbug,
                parent = self,
                required = defs.get('.required', False),
                dtype    = defs.get('.type'    , Null ),
                default  = defs.get('.default' , Null ),
                checks   = defs.get('.checks'  , []   ),
                **kwargs
            )

    def _setdefs(self, key, defs):
        """
        Sets keys from a definitions dictionary
        """
        value = Null
        if '.children' in defs:
            value = {}
            if defs.get('.type') == 'list':
                value = [{} for _ in range(defs.get('.number', 1))]
            defs = defs['.children']

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
            self._debug(1, '_update', f'Updating name from {old!r} to {new}')
            internal['_name'] = new

        # Update children
        self.deepUpdate()

    def deepUpdate(self):
        """
        Calls _update() on each Var/Sect in self. This will bring parent/child
        relationships in line with the current data, such as names and keys
        """
        for key, item in self.items(var=True):
            if not isinstance(item, (type(self), Sect, Var)):
                Logger.error(f'Should never encounter any type other Sect or Var, got: {type(item)} = {item}')
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
        self._debug(0, 'deepCopy', f'Creating deep copy using memo: {memo}')
        return copy.deepcopy(self, memo)

    def get(self, key, other=None, var=False):
        """
        """
        val = self._sect.get(key, other=Null, var=True)
        if val is not Null:
            if isinstance(val, Var):
                if var:
                    self._debug(3, 'get', f'[{key!r}] requested var, returning as: {val!r}')
                    return val
                self._debug(3, 'get', f'[{key!r}] returning value of var: {val!r}')
                return val.value
            self._debug(3, 'get', f'[{key!r}] is not a Var or Null, returning value: {val!r}')
            return val

        self._debug(3, 'get', f'[{key!r}] is Null, returning other: {other!r}')
        return other

    def keys(self):
        return self._sect.keys()

    def values(self):
        return self._sect.values()

    def items(self, var=False):
        """
        """
        self._debug(3, 'items', f'Returning items with var={var}')
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

    def toDict(self):
        """
        """
        data = {}
        for key, item in self._sect.items():
            data[key] = value = self[key]
            if isinstance(item, (type(self), Sect)):
                self._debug(0, 'toDict', f'Converting child Sect [{key!r}].toDict()')
                data[key] = value.toDict()
        return data

    def resetVars(self):
        """
        Runs reset on each Var
        """
        for key, item in self.items(var=True):
            if isinstance(item, Sect):
                item.resetVars()
            elif isinstance(item, Var):
                item.reset()
            else:
                Logger.error(f'Internal _sect has a value other than a Var or Sect: {key!r} = {item!r}')

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
            flag = ' '
            if defs.required:
                flag = '!'
            else:
                parent = sect._prnt
                while parent is not Null:
                    if parent._defs.required:
                        flag = '?'
                        break
                    parent = parent._prnt

            return (string, flag)


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
            value  = '\\' if var.value is Null else var.value
            string = var._offset + yaml.dump({key: value})[:-1]

            flag = ' '
            if var.required:
                flag = '!'
            else:
                parent = var.parent
                while parent is not Null:
                    if parent._defs.required:
                        flag = '?'
                        break
                    parent = parent._prnt

            return (string, flag)

        dump = [('generated:', ' ')]
        for key, item in self.items(var=True):
            if isinstance(item, Sect):
                # `key` is not in the item, create the "key: value" string for the row tuple
                string = f'{item._offset}{key}:'
                dump.append(rowFromSect(string, item))
                dump += item.dumpYaml(string=False)[1:]
            elif isinstance(item, Var):
                dump.append(rowFromVar(item))
            else:
                Logger.error(f'Internal _sect has a value other than a Var or Sect: {key!r} = {item!r}')

        # if string:
        #     dump = '\n'.join(dump)

        return dump

    def generateTemplate(self, file=None, style=None, comments='inline'):
        """
        Generates a YAML template file
        """
        dump = self.dumpYaml()

        if file:
            with open(file, 'w') as f:
                f.write(dump)
