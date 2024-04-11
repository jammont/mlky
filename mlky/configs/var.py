"""
Var objects are containers to hold values of a mlky Sect
"""
import copy
import logging
import re
import yaml

from . import (
    ErrorsDict,
    funcs,
    magic_regex,
    Null
)


Logger = logging.getLogger(__file__)
Types  = {
    'bool'   : bool,
    'bytes'  : bytes,
    'complex': complex,
    'dict'   : dict,
    'float'  : float,
    'int'    : int,
    'list'   : list,
    'set'    : set,
    'str'    : str,
    'tuple'  : tuple
}
TypeNames = {v: k for k, v in Types.items()}


def getType(dtype):
    """
    Helper function to convert strings to actual types
    """
    # Get actual type, else fallback to a registered function, else the parameter itself
    if isinstance(dtype, list):
        return [Types.get(val, funcs.Funcs.get(val, val)) for val in dtype]
    return Types.get(dtype, funcs.Funcs.get(dtype, dtype))


class Var:
    value    = Null
    debug    = set()
    missing  = True
    required = False
    strict   = False

    # Special flag to indicate when to skip checks
    _skip_checks = False

    # .reset() will replace magic strings "${...}", this will disable that
    _disable_reset_magics = False

    # Will only call replace on magic strings, not any value
    _replace_only_if_magic = True

    # Recursively call replace so values get populated correctly no matter order of operation
    _replace_recursively = True

    # Replace backslashes "\" with Null
    _replace_slash_null = True

    # Assists getValue() to retrieve a temporary value without setting it as .value
    _tmp_value = Null

    def __init__(self, name, key,
        value    = Null,
        default  = Null,
        example  = Null,
        dtype    = Null,
        subtypes = Null,
        required = False,
        missing  = False,
        checks   = [],
        strict   = False,
        debug    = -1,
        sdesc    = '',
        ldesc    = '',
        parent   = Null,
        replace  = True
    ):
        """
        Variable container object

        Parameters
        ----------
        strict: bool, default=False
            Checks dtype strictly, regardless if required or optional
        replace: bool, defaults=True
            Use the default Var.__setattr__ which will call replace() on `value`
            If `False`, circumvents Var.__setattr__ by using super().__setattr__
        """
        if isinstance(debug, int):
            debug = range(0, debug+1)

        self.name     = name
        self.key      = key
        self.default  = default
        self.example  = example
        self.dtype    = dtype
        self.subtypes = subtypes
        self.required = required
        self.missing  = missing
        self.checks   = checks
        self.strict   = strict
        self.debug    = set(debug)
        self.sdesc    = sdesc
        self.ldesc    = ldesc
        self.parent   = parent
        self.original = value

        if replace and not missing:
            # This will call replace() then validate()
            self.value = value
        else:
            # No replace(), takes as-is
            super().__setattr__('value', value)

    def __eq__(self, other):
        data = self.toDict()
        if isinstance(other, dict):
            return data == other
        elif isinstance(other, self.__class__):
            return data == other.toDict()
        return False

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        for key, val in self.__dict__.items():
            self._debug(1, '__deepcopy__', f'Deep copying __dict__[{key!r}] = {val!r}')
            new.__dict__[key] = copy.deepcopy(val, memo)
        return new

    def __reduce__(self):
        return (type(self), (
            self.name, self.key, self.value,
            self.default, self.dtype, self.required,
            self.missing, self.checks
        ))

    def deepReplace(self, value):
        """
        Calls reset on the children of this Var's value if it is a list type
        """
        for i, item in enumerate(value):
            if 'Sect' in str(type(item)):
                self._debug(2, 'deepReplace', f'Resetting {item}')
                item.resetVars()

            elif isinstance(item, str):
                new = self.replace(item)
                if new is not None:
                    self._debug(2, 'deepReplace', f'Replacing index [{i}] {item!r} with {new!r}')
                    value[i] = new

            elif isinstance(item, (list, tuple)):
                self._debug(2, 'deepReplace', f'Calling deepReplace on child list {item}')
                self.deepReplace(item)

    def __setattr__(self, key, value):
        """
        """
        if key == 'value':
            # Reset this if it was set elsewhere when the Var.value is changed
            self._skip_checks = False

            # Lists to Sects disabled, perform a deep replacement
            if isinstance(value, (list, tuple)):
                self.original = copy.deepcopy(value)
                self.deepReplace(value)
            else:
                # Always call to see if this value should be replaced
                new = self.replace(value)
                if new is not None:
                    self.original = value
                    value = new

            # Replacement may cause a value to become Null, this is always considered "missing"
            if value is Null:
                self.missing = True
            else:
                self.missing = False

            # Non-empty dict means errors found
            errs = self.validate(value).reduce()
            if errs:
                Logger.error(f'Changing the value of this Var({self.name}) to will cause validation to fail. See var.validate() for errors')

        elif key == 'dtype':
            value = getType(value)

        # Cast subtype dtypes to real types
        elif key == 'subtypes':
            for sub in value:
                if 'dtype' not in sub:
                    msg = f'Defs keys with multiple types must define the dtype for each explicitly. Missing for {key}[{i}]'
                    self._log('e', '__setattr__', msg)
                    raise AttributeError(msg)

                sub['dtype'] = getType(sub['dtype'])

        super().__setattr__(key, value)

    def __repr__(self):
        return f'<Var({self.key}={self.value!r})>'

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
        return self

    @property
    def _offset(self):
        """
        Offset in spaces to denote hierarchical level
        """
        name = len(self.name.split('.'))
        if isinstance(self.key, int):
            name += 1
            key = 1
        else:
            key = len(self.key.split('.'))

        return '  ' * (name - key)

    def _debug(self, level, func, msg):
        """
        Formats debug messages
        """
        message = f'{self._offset}<{type(self).__name__}>({self.name}).{func}() {msg}'
        if level == 'e':
            Logger.error(message)
        elif level in self.debug or func in self.debug:
            Logger.debug(message)

    def _update(self, key, parent):
        """
        Updates values of this Var given a new parent Sect
        """
        self.debug = parent._dbug

        if key != self.key:
            self._debug(1, 'update', f'Updating key from {self.key!r} to {key}')
            self.key = key

        old = self.name
        new = parent._subkey(key)
        if new is not Null and new != old:
            self._debug(1, '_update', f'Updating name from {old!r} to {new}')
            self.name = new

        self.parent = parent

    def toDict(self):
        return self.__dict__

    def deepCopy(self, memo=None):
        return copy.deepcopy(self, memo)

    def checkType(self, value=Null, strict=False):
        """
        Checks a given value against the type set for this object.

        Parameters
        ----------
        value: any, default=Null
            Value to test against. If left as default Null, will use the Var.value
        strict: bool, defaults=False
            Sets strict for this call only
        """
        if value is Null:
            value = self.getValue()

        if all([
            not (self.strict or strict), # Strict cases always check dtype
            not self.required,           # Not required to be set
            value is Null                # Already a null value, possibly inherently null
        ]):
            return True

        return funcs.getRegister('check_dtype')(value, self.dtype)

    def validate(self, value=Null, strict=False, **kwargs):
        """
        Validates a value against this variable's checks

        Parameters
        ----------
        value: any, defaults=Null
            Value to validate. If left as default Null, will use the Var.value
        strict: bool, defaults=False
            Sets strict for this call only

        Returns
        -------
        errors: mlky.ErrorsDict or True
            If all checks pass, returns True, otherwise returns an Errors
            object. Essentially the same as a dict. Each key is the check name
            and the value is either True for passing, a string for a single
            failure, or a list of strings for multiple failures. This is a
            custom dict that implements the reduce() function that will only
            return checks that failed by removing any checks wasn't a str or
            list. This should help filter bad returns from custom check
            functions as well.
        """
        if value is Null:
            value = self.getValue()
        else:
            self._tmp_value = value

        # Custom dict, can use e.reduce() to remove e[check]=True
        errors = ErrorsDict()

        # Special cases may not want to execute the checks
        if self._skip_checks:
            self._debug(0, 'validate', '_skip_checks enabled, returning no errors')
            return errors

        # Don't run any checks if the key was missing
        if self.missing and not (self.strict or strict):
            if self.required:
                errors['required'] = 'This key is required to be manually set in the config'
            self._debug(0, 'validate', f'This Var is missing and not strict')
            return errors

        # Check the type before anything else
        errors['type'] = self.checkType(value, strict)

        for check in self.checks:
            args   = []
            kwargs = {}
            if isinstance(check, dict):
                (check, args), = list(check.items())
                if isinstance(args, dict):
                    kwargs = args
                    args = []

            self._debug(0, 'validate', f'Running check {check}(args={args}, kwargs={kwargs})')
            errors[check] = funcs.getRegister(check)(self, *args, **kwargs)

        # Validate child objects if this is a list
        if isinstance(value, list):
            for item in value:
                if hasattr(item, 'validate'):
                    errors[item._f.name] = item.validate()

        # Reset at the end
        self._tmp_value = Null

        # self._debug(0, 'validate', f'Errors reduced: {errors.reduce()}') # Very spammy, unsure about usefulness
        return errors

    def reset(self):
        """
        Resets this Var's value to its original. This is primarily useful to
        reset all Vars to trigger replacements after a Config finishes
        initialization
        """
        value = self.getValue()

        if value is not self.original:
            self._debug(0, 'reset', f'Resetting from {value} to {self.original}')
            self.value = self.original
        elif isinstance(value, str) and value.startswith('$'):
            if not self._disable_reset_magics:
                self._debug(0, 'reset', f'Current value is a magic, resetting to call replacement')
                self.value = value

    def applyDefinition(self, defs):
        """
        Applies values from a definitions object
        """
        value = self.getValue()
        for key, val in defs.items():
            if key == 'items':
                for subval in value:
                    if subval is not Null and hasattr(subval, 'applyDefinition'):
                        name = subval._f.name
                        self._debug(0, 'applyDefinition', f'Applying definitions to child objects: {name}')
                        subval.applyDefinition(val.get(name, val))
            else:
                self._debug(0, 'applyDefinition', f'{key} = {val!r}')
                setattr(self, key, val)

                if key == 'default' and self.original is Null:
                    self._debug(0, 'applyDefinition', f'Original is Null and default provided, setting original to default')
                    setattr(self, 'original', val)

    def replace(self, value):
        """
        mlky replacement magic to support independent Sect instances

        Work in progress
        """
        if isinstance(value, str):
            # Allow "\" values to be passed through to the replace function which will be replaced with Null
            if self._replace_slash_null and value == '\\':
                pass

            # Ensure a string has a magic
            elif self._replace_only_if_magic:
                if not re.findall(magic_regex, value):
                    return

        # Call replacement on string types only if option is set
        elif self._replace_only_if_magic:
            return

        # Find the root parent
        parent = self.parent
        while parent._prnt:
            parent = parent._prnt

        # TODO: This is broken, just default to the global instance until further research
        parent = None

        replacement = funcs.getRegister('config.replace')(value, parent, dtype=self.dtype, callResets=self._replace_recursively, _debug=self._debug)
        if replacement is not value:
            self._debug(0, 'replace', f'Replacing {value!r} with {replacement!r}')
            return replacement

    def getValue(self, default=True, example=False):
        """
        Returns this Var's value. If it is Null and default is enabled, returns the
        default value instead.

        Parameters
        ----------
        default: bool, default=True
            If .value is Null, return .default
            If this is false, always return .value
        example: bool, default=False
            Override and return the example value
        """
        if example:
            return self.example

        # If a user passes in a value to validate(), return that on any call to this function
        # This helps registered functions retrieve a temporary value instead
        if self._tmp_value is not Null:
            return self._tmp_value

        # Otherwise if default is enabled, return that
        if default and self.value is Null:
            return self.default

        return self.value

    def getSubType(self, value):
        """
        Retrieves the subtype definition if the input value matches to one

        Parameters
        ----------
        value: any
            Value to check

        Returns
        -------
        False or dict
            The defs dict for the subtype if it matches the value type, False otherwise
        """
        for sub in self.subtypes:
            if isinstance(value, sub['dtype']):
                return sub
        return False

    def dumpYaml(self, key=None, example=False, **kwargs):
        """
        Serialize the object to YAML format.

        Parameters
        ----------
        key: str or None, optional
            The key to use in the YAML output. If None, the name of the object will be used as the key.
        example: bool, default=False
            Use example values instead of actual or default values
        **kwargs: dict
            Ignore other kwargs that may be passed by a Sect parent but are unused by Var objects

        Returns
        -------
        list
            A list containing the YAML representation of the object
        """
        if key is None:
            key = self.name

        # Cast dtype back to str name
        dtype = self.dtype
        if isinstance(dtype, list):
            dtype = ', '.join([TypeNames.get(item, str(item)) for item in dtype])
        else:
            dtype = TypeNames.get(dtype, str(dtype))

        # Change the flag comment if set
        flag = ' '
        if self.required:
            flag = '!'
        else:
            parent = self.parent
            while parent is not Null:
                if parent._defs.get('required'):
                    flag = '?'
                    break
                parent = parent._prnt

        value = self.getValue(example=example)

        lines = []
        if example:
            # Multiple examples
            if isinstance(value, list):
                for val in value:
                    if isinstance(val, dict):
                        ...
            else:
                line = yaml.dump({key: value})[:-1]


        elif isinstance(value, list):
            line = f'{key}:'
            if value:
                for val in value:
                    if val is Null:
                        # Replace Null values with backslash
                        lines.append(['- \\'])
                    elif hasattr(val, 'dumpYaml'):
                        dump = val.dumpYaml('', string=False)
                        dump[0][0] = '- ' + dump[0][0]
                        lines += dump
                    else:
                        lines.append(['- ' + yaml.dump(val).split('\n')[0]])
            else:
                line = f'{key}: []'
        else:
            if value is Null:
                value = '\\'
            line = yaml.dump({key: value})[:-1]

        # Apply spacing offset
        if lines:
            for i, child in enumerate(lines):
                lines[i][0] = '  ' + child[0]

        return [[line, flag, dtype or '', self.sdesc]] + lines
