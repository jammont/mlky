"""
Var objects are containers to hold values of a mlky Sect
"""
import copy
import logging

from . import (
    ErrorsDict,
    funcs,
    Null
)


Logger = logging.getLogger(__file__)


class Var:
    value    = Null
    debug    = set()
    missing  = True
    required = False

    def __init__(self, name, key,
        value    = Null,
        default  = Null,
        dtype    = Null,
        required = False,
        missing  = False,
        checks   = [],
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
        replace: bool, defaults=True
            Use the default Var.__setattr__ which will call replace() on `value`
            If `False`, circumvents Var.__setattr__ by using super().__setattr__
        """
        if isinstance(debug, int):
            debug = range(0, debug+1)

        self.name     = name
        self.key      = key
        self.default  = default
        self.dtype    = dtype
        self.required = required
        self.missing  = missing
        self.checks   = checks
        self.debug    = set(debug)
        self.sdesc    = sdesc
        self.ldesc    = ldesc
        self.parent   = parent
        self.original = value

        if replace:
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

            # No longer missing if it's set
            self.missing = False

            # Non-empty dict means errors found
            if self.validate(value).reduce():
                Logger.error(f'Changing the value of this Var({self.name}) will cause validation to fail. See var.validate() for errors.')

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
        if level in self.debug or func in self.debug:
            Logger.debug(f'{self._offset}<{type(self).__name__}>({self.name}).{func}() {msg}')

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

    def checkType(self, value=Null):
        """
        Checks a given value against the type set for this object.
        """
        if value is Null:
            value = self.value

        # Not required, already a null value (either set in config explicitly as null or was inherently null)
        if not self.required and value is Null:
            return True

        return funcs.getRegister('check_dtype')(value, self.dtype)

    def validate(self, value=Null):
        """
        Validates a value against this variable's checks

        Parameters
        ----------
        value: any, defaults=Null
            Value to validate. If left as default Null, will use the Var.value

        Returns
        -------
        errors: mlky.Errors or True
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
            value = self.value

        # Custom dict, can use e.reduce() to remove e[check]=True
        errors = ErrorsDict()

        # Don't run any checks if the key was missing
        if self.missing:
            if self.required:
                errors['required'] = 'This key is required to be manually set in the config'
            self._debug(0, 'validate', f'This Var is missing and not required')
            return errors

        # Check the type before anything else
        errors['type'] = self.checkType()

        for check in self.checks:
            args   = []
            kwargs = {}
            if isinstance(check, dict):
                (check, args), = list(check.items())
                if isinstance(args, dict):
                    kwargs = args
                    args = []

            errors[check] = funcs.getRegister(check)(self, *args, **kwargs)

        # self._debug(0, 'validate', f'Errors reduced: {errors.reduce()}') # Very spammy, unsure about usefulness
        return errors

    def reset(self):
        """
        Resets this Var's value to its original. This is primarily useful to
        reset all Vars to trigger replacements after a Config finishes
        initialization
        """
        if self.value is not self.original:
            self._debug(0, 'reset', f'Resetting from {self.value} to {self.original}')
            self.value = self.original

    def applyDefinition(self, defs):
        """
        Applies values from a definitions object
        """
        for key, val in defs.items():
            self._debug(0, 'applyDefinition', f'{key} = {val!r}')
            setattr(self, key, val)

    def replace(self, value):
        """
        mlky replacement magic to support independent Sect instances

        Work in progress
        """
        # Find the root parent
        parent = self.parent
        while parent._prnt:
            parent = parent._prnt

        # TODO: This is broken, just default to the global instance until further research
        parent = None

        replacement = funcs.getRegister('config.replace')(value, parent)
        if replacement is not value:
            self._debug(0, 'replace', f'Replacing {value!r} with {replacement!r}')
            return replacement
