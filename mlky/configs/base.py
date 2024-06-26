"""
"""
import copy
import logging
import re

from .funcs  import ErrorsDict, getRegister, reportErrors
from .null   import Null
from ..utils import printTable


Logger = logging.getLogger('mlky/base')

SectTypes = dict(
    dict = lambda item: 'DictSect' in str(type(item)),
    list = lambda item: 'ListSect' in str(type(item)),
    var  = lambda item: 'Var'      in str(type(item)),
)
def isSectType(item, kind=None):
    """
    Utility to checks if a given item is a Sect type object
    """
    if kind is None:
        kind = list(SectTypes)

    if isinstance(kind, list):
        return any([SectTypes[k](item) for k in kind])

    return SectTypes[kind](item)


class BaseSect:
    """
    Section base class
    """
    _logger   = Logger
    _labels   = True  # Toggle labels in __repr__
    _label    = ''    # Object label, defined by subclass
    _data     = None  # Internal formatted data
    _input    = None  # Original input data
    _key      = None  # Key name of self
    _parent   = None  # Parent object
    _name     = ''    # Full name of self (dot notational)
    _offset   = ''    # Hierarchical offset for padding
    _debug    = set() # Debug levels and names
    _nulls    = True  # Return Null values as defaults instead of Nones
    _defs     = {}    # Definition for this object to control validation
    _missing  = False # Only set by a defs object
    _dtype    = ''    # Data type for this object
    _override = None  # CLI override data

    # ListSect flags
    _patchAppend    = False

    # Var flags
    _coerce         = True
    _interpolate    = True
    _relativity     = True
    _convertSlashes = True
    _nullsEqMissing = False


    def __init__(self, _data, key='', parent=None, **kwargs):
        """
        Initializes a Sect object. The subclass must define a _subinit function to
        finalize initialization including the setting of self._data.

        Parameters
        ----------
        _data : any
            Data to set for this object. Type varies per subclass
        key : str, default=''
            Key name of this object
        parent : SectType, default=None
            The parent Sect object of this object
        **kwargs : dict
            Any additional key-word arguments for a subclass._subinit function
        """
        self._key    = key
        self._parent = parent
        self._input  = _data

        # Create a unique instance of the _data object before it becomes populated
        self._data = copy.copy(self._data)

        # Set first for any downstream functions
        if '_debug' in kwargs:
            self['_debug'] = kwargs['_debug']
            del kwargs['_debug']

        # Additional flags that may be relevant to some subclass
        for key, value in kwargs.items():
            # Only set if it already exists
            if hasattr(self, key):
                self[key] = value

        self._setName()

        # Initialize per the subclass rules
        self._log(3, '__init__', 'Initializing')
        self._subinit(_data, **kwargs)
        self._log(3, '__init__', 'Finished')

        # Build the defs after self._data is populated which may influence how the defs populate
        self._buildDefs()

        if self._override:
            self._log(3, '__init__', 'Overriding keys')
            for key, value in self._override:
                self.overrideKey(key, value)


    def __bool__(self):
        return bool(self._data)


    def __call__(self, *args, **kwargs):
        """
        """
        if args or kwargs:
            self._log(0, '__call__', 'Reinitializing with new input')

            new = self._sect(*args, **kwargs)
            super().__setattr__('__dict__', new.__dict__)
            super().__setattr__('__class__', new.__class__)

        return self


    def __contains__(self, key):
        """
        """
        return key in self._data


    def __deepcopy__(self, memo):
        """
        Creates a deep copy of the object
        """
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new

        for key, val in self.__dict__.items():
            self._log(1, '__deepcopy__', f'Deep copying __dict__[{key!r}] = {val!r}')
            new.__dict__[key] = copy.deepcopy(val, memo)

        return new


    def __delitem__(self, key):
        if key in self:
            del self._data[key]


    def __eq__(self, other):
        """
        Tests equality. Subclass must define toPrim for this to work

        Parameters
        ----------
        other : any
            Other object to test equality with

        Returns
        -------
        bool
        """
        if isSectType(other):
            other = other.toPrim(recursive=True)

        return self.toPrim(recursive=True) == other


    def __iter__(self):
        raise NotImplementedError(f'Subclass {self.__class__} must define function __iter__')


    def __len__(self):
        return len(self._data)


    def __getattr__(self, key, other=Null, var=False):
        # Calls that should not exist such as _ipython_canary_method_should_not_exist_
        if isinstance(key, str) and key.startswith('_') and key.endswith('_'):
            raise AttributeError(key)

        self._log(3, '__getattr__', f'Retrieve [{key!r}]')
        # self._buildDefs()

        try:
            item = self._data[key]
            if var or not isSectType(item, 'var'):
                self._log(3, '__getattr__', f'[{key!r}] Returning item directly: {item}')
                return item
            self._log(3, '__getattr__', f'[{key!r}] Returning item.getValue(): {item}')
            return item.getValue()
        except:
            self._log(3, '__getattr__', f'[{key!r}] Returning other: {other}')
            return self._NullOrNone(other)


    def __getitem__(self, key):
        return self.__getattr__(key)


    def __getstate__(self):
        return self.__dict__.copy()


    def __setstate__(self, state):
        self.__dict__.update(state)


    def __or__(self, other):
        """
        Patches a copy of this object with a patch-compatible object. Compatibility
        varies per subclass.

        Parameters
        ----------
        other : any
            Patch-compatible object

        Returns
        -------
        self.applyPatch : SectType
            Returns a patched version of this object
        """
        if not self.patchCompatible(other):
            raise TypeError(f'Incompatible object type for patching: {type(other)}')

        return self.applyPatch(other, inplace=False)


    def __setattr__(self, key, value):
        """
        Sets attributes on the object depending on the input key and value. If the key
        is a known private key, sets the value directly. Otherwise, casts the value to
        a Sect type if it is not already and then figures out how to call self._addData
        depending on a few rules.

        Parameters
        ----------
        key : str
            Key of attribute to set
        value : any
            Value to set
        """
        # Internal private key, set directly
        if hasattr(type(self), str(key)):
            if key == '_debug':
                self.setDebug(value)
            else:
                self.__dict__[key] = value
            return

        if isSectType(value):
            # Update the existing object to be a child of this
            self._log(3, '__setattr__', f'Updating existing SectType to child of this')
            value.updateChild(parent=self, key=key)
        else:
            # Cast the new value into the appropriate container object
            self._log(3, '__setattr__', f'Creating a new object')
            value = self._makeObj(key, value)

        # If it already exists, set the value
        this = self.__getattr__(key, var=True)

        if isSectType(value, 'var') and isSectType(this):
            # Var replacing Var, update the value of the existing
            if isSectType(this, 'var'):
                self._log(3, '__setattr__', f'Updating Var {this} = {value._data!r}')
                this._addData(value._data)

            # Var replacing Dict or List, replace outright
            else:
                self._log(3, '__setattr__', f'Replacing child {key} = {value}')
                self._addData(key, value)

        # New value is Dict or List
        else:
            self._log(3, '__setattr__', f'Adding new child {key} = {value}')
            self._addData(key, value)


    def __setitem__(self, key, value):
        self.__setattr__(key, value)


    def __repr__(self):
        # Disable the labels if set
        if self._labels is False:
            self._label = ""
        return f"{self._label}{self._data!r}"


    def _addData(self, key, value):
        """
        Adds to self._data. Must be implemented by the subclass.

        Parameters
        ----------
        key : str
            Key to assign
        value : any
            Value to add
        """
        raise NotImplementedError(f'Subclass {self.__class__} must define function _addData')


    def _applyDefs(self):
        """
        Applies the defs to this object. Must be implemented by the subclass
        """
        raise NotImplementedError(f'Subclass {self.__class__} must define function _applyDefs')


    def _buildDefs(self):
        """
        Builds the defs for this object per the parent's defs
        """
        # Root object doesn't build defs, uses the initially passed in dict
        if self._parent is None:
            return self._applyDefs()

        self._log(0, '_buildDefs', f'Building defs')
        parentDefs = self._parent._defs

        if not parentDefs:
            self._log(0, '_buildDefs', f'No parent defs, skipping')
            return

        key  = f'.{self._key}'
        defs = parentDefs.get(key, self._sect())

        cases = parentDefs.get('match', [])
        for case in cases:
            for required in ('case', 'key'):
                if required not in case:
                    raise AttributeError(f'The `{required}` must be defined for each item in the match list, please check: {case}')

            dtype = case['case']
            key   = str(case['key'])
            val   = case.get('value')

            # Match to the case dtype
            if self._dtype == dtype:
                if key == '*':
                    self._log(0, '_buildDefs', f'Matched to case: <{dtype}>[{key}]')
                    defs = defs | case

                elif getattr(self, key) == val:
                    self._log(0, '_buildDefs', f'Matched to case: <{dtype}>[{key}] = {val}')
                    defs = defs | case

        if self._defs != defs:
            self._log(0, '_buildDefs', f'Setting defs: {defs}')
            self._defs = defs
            self._applyDefs()

        else:
            self._log(0, '_buildDefs', f'Same defs as presently set')


    def _getChildren(self):
        """
        Return this object's children as Var objects. Must be implemented by the
        subclass.

        Returns
        -------
        list
            List of Var objects that are children of this
        """
        raise NotImplementedError(f'Subclass {self.__class__} must define function _getChildren')


    def _hasTags(self, tags):
        """
        Checks if this object has desired tags.

        Parameters
        ----------
        tags : list
            Tags to check against self._defs['tags']

        Returns
        -------
        bool
            True if any tag in the list is assigned to this object
        """
        this = self._defs.get('tags', [])
        tags = set(tags).intersection(this)
        return bool(tags)


    def _log(self, level, caller, message):
        """
        Logger function

        Parameters
        ----------
        level : int
            Log level for the message
        caller : str
            Function that the message sources from
        message : str
            Message to log
        """
        if level == 'e':
            self._logger.error(f'{self._label}({self._name}).{caller}: {message}')
        elif level in self._debug or caller in self._debug:
            self._logger.debug(f'{caller:15} | {level} | {self._label}({self._name}) {message}')


    def _makeObj(self, key, value):
        """
        Creates a child object of this object and passes the settings along

        Parameters
        ----------
        key : str
            Key to assign
        value : any
            Value to add

        Returns
        -------
        obj : SectType
        """
        # Import here to avoid circular imports
        from .sect import Switch

        obj = Switch(key, value, self,
            ## Pass these flags onto children
            _nulls          = self._nulls,
            # List
            _patchAppend    = self._patchAppend,
            # Var
            _debug          = self._debug,
            _labels         = self._labels,
            _coerce         = self._coerce,
            _interpolate    = self._interpolate,
            _relativity     = self._relativity,
            _convertSlashes = self._convertSlashes,
            _nullsEqMissing = self._nullsEqMissing,
        )

        # obj.updateDefs(self._defs)

        return obj


    def _mutate(self, kind):
        """
        Mutates this object into a new Sect object depending on the given kind

        This is an experimental feature and may cause cascading issues
        """
        if kind == 'dict':
            value = {}
        elif kind == 'list':
            value = []
        else:
            value = Null

        # Construct the new object
        new = self._makeObj(self._key, value)
        new._parent = self._parent
        if self._parent:
            new.updateDefs(self._parent._defs)

        self._log(1, '_mutate', f'Mutating to {new}')
        super().__setattr__('__dict__', new.__dict__)
        super().__setattr__('__class__', new.__class__)


    def _NullOrNone(self, value=None):
        """
        Always return a value that is not a Null. If Null, use either Null if they are
        enabled, otherwise return None

        Parameters
        ----------
        value : any, default=None
            If Null, refer to _nulls to return either Null or None

        Returns
        -------
        value or Null or None
        """
        if value is Null:
            if self._nulls:
                return Null
            return None
        return value


    def _sect(self, *args, **kwargs):
        """
        Makes a new, independent Sect object

        Parameters
        ----------
        *args : list
            Any additional arguments passed directly to Sect(*args)
        **kwargs : dict
            Any additional key-word arguments passed directly to Sect(**kwargs)

        Returns
        -------
        Sect(*args, **kwargs)
            The newly create Sect object
        """
        # Import here to avoid circular imports
        from .sect import Sect
        return Sect(*args, **kwargs)


    def _setName(self):
        """
        Sets the dot-notational name for the object
        """
        name = self._key

        if isSectType(self._parent, 'dict'):
            name = f'{self._parent._name}.{name}'
        elif isSectType(self._parent, 'list'):
            name = f'{self._parent._name}[{name!r}]'

        self._name   = str(name)
        self._offset = ' ' * len(self._name.split('.'))


    def deepCopy(self, memo=None):
        """
        Creates a deep copy of the object
        """
        self._log(0, 'deepCopy', f'Creating deep copy using memo: {memo}')
        return copy.deepcopy(self, memo)


    @staticmethod
    def enableLogging():
        """
        Utility method to easily enable logging for a user
        """
        logging.basicConfig(level=logging.DEBUG)


    def get(self, key, other=Null, **kwargs):
        """
        Retrieves a child at a key.

        Parameters
        ----------
        key : any
            Key-name of the child
        other : any, default=Null
            If child doesn't exist, return this value instead

        Returns
        -------
        any
            The child at key, otherwise the other value
        """
        return self.__getattr__(key, other, **kwargs)


    def overrideKey(self, path, value):
        """
        Follows a path to either override an existing key or create the key at the
        path. A path is dot-notational for dicts and brackets for lists, examples:

        "abc.def.g" maps to:
        abc:
          def:
            g

        "abc[0].def[1].g" maps to:
        abc:
          - def:
            - ... # 0
            - g   # 1

        Parameters
        ----------
        path : str
            Path to a key to override. If this path does not exist, it will be created
        value : any
            The value to set
        """
        if isinstance(path, str):
            # Remove relative pathing
            if path.startswith('.'):
                path = path[1:]

            # path = path.split('.')
            path = re.findall(r'[^.[\s]+', path)

        key = path[0]
        self._log(0, 'overrideKey', f'Overriding key {key!r}')

        # Match to a list item
        isList = False
        if key.endswith(']'):
            isList = True
            key = key[:-1]

        if key.isnumeric():
            key = int(key)

        child = self.get(key, var=True)

        # If the child already exists, keep searching for the correct object to override
        if isSectType(child):
            self._log(0, 'overrideKey', 'Key exists, overriding child')
            child.overrideKey(path[1:], value)
        else:
            # Create a list or dict type
            if len(path) > 1:
                if isList:
                    self._log(0, 'overrideKey', 'Creating new child list')
                    self[key] = []
                else:
                    self._log(0, 'overrideKey', 'Creating new child dict')
                    self[key] = {}
                self[key].overrideKey(path[1:], value)
            # Create a Var
            else:
                if isList:
                    self._log(0, 'overrideKey', f'Creating new child as list [{value!r}]')
                    self[key] = [value]
                else:
                    self._log(0, 'overrideKey', f'Creating new child [{value!r}]')
                    self[key] = value


    def parsePatch(self, patch):
        """
        Parses a patch string or list into a list for determining patching order.
        Patches can be defined as:
            str  - "sectionA<-sectionB", sectionB patches SectionA
            list - ["sectionA", "sectionB"], sectionB patches SectionA
        If a section defines the special key "mlky.patch" then that will be recursively
        parsed and inserted into the patchList.

        sectionA:
            mlky.patch: default

        patch="sectionA<-sectionB" will parse to ["default", "sectionA", "sectionB"]

        Parameters
        ----------
        patch : str, list
            The given patch order

        Returns
        -------
        patchList : list
            List of sections to patch in order
        """
        if patch is None:
            return

        if isinstance(patch, str):
            patch = patch.split('<-')

        patchList = []
        if isinstance(patch, list):
            for section in patch:
                if section not in self:
                    self._log('e', 'parsePatch', f'Section not found: {section!r}')
                else:
                    sect = self[section]

                    # Insert any dependency patches defined in the section
                    patches = sect.get('mlky.patch')
                    if patches:
                        patches = self.parsePatch(patches)
                        patchList += patches
                        del sect['mlky.patch']

                    patchList.append(section)
        else:
            self._log('e', 'parsePatch', f'Could not parse patch information, please refer to docs: {patch!r}')

        self._log(0, 'parsePatch', f'Parsed patch: {patchList}')
        return patchList


    def patchCompatible(self, item):
        """
        Checks if an object is compatible to be patched with this object. Should be
        defined by a subclass if it implements applyPatch()

        Parameters
        ----------
        item : any
            Check if this is a patch-compatible object

        Returns
        -------
        bool
        """
        # Unless implemented, inherently false
        return False


    def setDebug(self, levels):
        """
        Sets the debug levels for this object

        Parameters
        ----------
        levels : str, int, list
            Levels to set. If str, converts to list. If int, converts to
            range(0, int+1). If list, takes as-is
        """
        if isinstance(levels, str):
            levels = [levels]

        if isinstance(levels, int):
            levels = range(0, levels+1)

        if hasattr(levels, '__iter__'):
            levels = set(levels)

        if levels is None:
            levels = set()

        # Bypass __setattr__ to prevent recursion
        self.__dict__['_debug'] = levels


    def touchVars(self):
        """
        Touches the getValue function of all Vars recursively to retrieve their actual
        values
        """
        for child in self._getChildren():
            if isSectType(child, 'var'):
                child.getValue()
            else:
                child.touchVars()

        return self


    def toYaml(self, string=True, file=None, header=True, tags=[], blacklist=False, nulls=True, comments='inline', space=False, **kwargs):
        """
        Converts this object to YAML

        Parameters
        ----------
        string : bool, default=True
            Converts the formatted list of tuples to a string ready for printing or
            writing to file
        file : str, default=None
            Write the YAML to this file
        header : bool, default=True
            Adds the mlky header and sets the top level section as "generated"
        tags : list
            List of tags to include in the output. This acts as a whitelist where all
            other tags will be excluded
        blacklist : bool
            All tags in the `tags` parameter will be blacklisted instead, where tags
            not in this list will be accepted
        nulls : bool, default=True
            Include Vars that return Null. Set False to exclude these
        comments : str, default='inline'
            Comment styling:
                - inline = key: value # comment
                - above  = Comment line above the key: value (Not Implemented)
                - None   = Comments removed
        space : bool, default=False
            Adds a blank line space between lines
        **kwargs : dict
            Additional key-word arguments that apply to specific Sect types:
            List:
                listStyle : ['short', 'long'], default='long'
                    How to stylize the lists. Long puts each item on its own line.
                    Short will condense the items to a single line between [] brackets.
                    Short only works if all items of the list are Var types (not lists
                    or dicts)
        """
        # Determine if to convert this obj to YAML depending on the tags
        if tags:
            hasTags = self._hasTags(tags)
            if blacklist:
                if hasTags:
                    return []
            elif not hasTags:
                return []

        # Convert self to YAML
        offset = 2
        if isSectType(self._parent, 'list'):
            line = '- '
        elif isSectType(self._parent, 'dict'):
            line = f'{self._key}:'
        elif header:
            line = 'generated:'
        else:
            line = ''
            offset = 0

        defs = self._defs
        if defs is None:
            defs = {}

        flag  = '*' if defs.get('required') else ' '
        dtype = self._dtype
        sdesc = defs.get('sdesc', '')
        if line:
            line = [line, flag, dtype, sdesc]

        # Convert the children to YAML
        lines = []
        for child in self._getChildren():
            lines += child.toYaml(
                string    = False,
                tags      = tags,
                blacklist = blacklist,
                nulls     = nulls,
                comments  = comments,
                space     = space,
                **kwargs
        )

        # Apply offsetting to children
        for child in lines:
            child[0] = ' '*offset + child[0]

        # No children were provided, set as an empty object
        if not lines:
            line[0] += f' {self._data}'

        # Insert this line before the children after formatting
        if line:
            lines = [line] + lines

        # Format the comments
        if comments == 'above':
            # # flag | dtype | sdesc
            # key: value

            hold = []
            for line in lines:
                offset = ' ' * (len(line[0]) - len(line[0].lstrip()))

                # Add spacing
                if space:
                    offset = f'\n{offset}'

                hold.append([offset + '# ' + ' | '.join(line[1:])])
                hold.append([line[0]])

            lines = hold

        else:
            if comments == 'inline':
                pass # lines list is already formatted properly to this style
            elif comments in (None, False):
                lines = [[line[0]] for line in lines]

            # Add spacing
            if space:
                for line in lines:
                    line[0] = '\n' + line[0]

        # Format
        if string or file:
            yaml = '\n'.join(
                printTable(lines, columns = {
                        0: {'delimiter': '#'},
                        1: {'delimiter': '|'},
                    },
                    print    = None,
                    # truncate = truncate
                )
            )

            if file:
                with open(file, 'w') as f:
                    f.write(yaml)

            if string:
                return yaml

        return lines


    def updateChild(self, parent, key):
        """
        Updates self as a child of another SectType object

        Parameters
        ----------
        parent : SectType
            The sect object to set as the parent
        key : str
            The key that the parent has for this child
        """
        self._log(0, 'updateChildren', f'Updating as key {key!r} with parent {parent._name!r}')
        self._key    = key
        self._parent = parent

        self._setName()
        self.setDebug(parent._debug)

        self.updateChildren()


    def updateChildren(self):
        """
        Updates child objects with their expected key and this object as the parent.
        Must be implemented by subclass
        """
        raise NotImplementedError(f'Subclass {self.__class__} must define function updateChildren')


    def updateDefs(self, defs):
        """
        Updates the defs for this object by parsing the parent's defs and retrieving
        the appropriate rules. Must be implemented by subclass
        """
        raise NotImplementedError(f'Subclass {self.__class__} must define function updateDefs')


    def validateObj(self, report=True, asbool=True, **kwargs):
        """
        Validates a Sect and its children

        Parameters
        ----------
        report: bool, default=True
            Reports the (reduced) errors to logger.error in a pretty format
        asbool: bool, default=True
            Returns the errors dict as an inverted boolean, True for no errors, False for errors
        **kwargs: dict
            Additional key-word arguments to pass onto child validations. These include:
            - strict: bool, default=False
                ...

        Returns
        -------
        errors: dict
            Errors dictionary that contains all the checks for each key. This is a
            special dictionary that can be reduced using errors.reduce() to only see
            checks that failed validation
        """
        errors = ErrorsDict()

        # Validate this Sect using children assigned to specific tags
        for check in self._defs.get('checks', []):
            (check, args), = list(check.items())

            if isinstance(args, str):
                args = [args,]

            children = self._getChildren()
            for tag in args:
                tagged = []
                for child in children:
                    if tag in child._defs.get('tags', []):
                        tagged.append(child)

                errors[f'{check}[{tag}]'] = getRegister(check)(tagged)

        # Validate children
        for child in self._getChildren():
            errors[child._name] = child.validateObj(report=False, asbool=False, **kwargs)

        if report:
            reportErrors(errors.reduce())

        if asbool:
            return not bool(errors.reduce())

        return errors
