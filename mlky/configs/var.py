"""
"""
import logging

from functools import partial

from .base        import BaseSect, isSectType
from .funcs       import ErrorsDict, getRegister
from .interpolate import interpolate
from .null        import Null
from .types       import getType


Logger = logging.getLogger('mlky/var ')


class Var(BaseSect):
    """
    Container for variable objects
    Bases from BaseSect but acts differently than other Sect classes
    """
    _logger     = Logger
    _label      = 'V='
    _data       = Null
    _dtype      = Null
    _tmpVal     = Null
    _isDefault  = False
    _multiTyped = False
    _original   = Null

    # Attempt to coerce values (self._data) to the expected dtype
    _coerce = True

    # Interpolate string values on access .getValue()
    _interpolate = True

    # Use relative pathing with interpolation; disabling will convert everything to absolute pathing
    _relativity = True

    # Auto converts backslashes "\" to Null
    _convertSlashes = True

    # Skips validation if called
    _skipValidate = False

    # If a value is Null, sets self as missing
    _nullsEqMissing = False


    def _subinit(self, _data, **kwargs):
        """
        """
        # Overwrite the existing Var with the new one
        if isinstance(_data, Var):
            self.__dict__ = _data.__dict__
            value = value._data

        if self._dtype is Null:
            self._dtype = getType(type(_data))

        self._data = _data


    def _addData(self, value):
        """
        """
        self._data      = value
        self._missing   = False
        self._isDefault = False

        self._buildDefs()


    def _applyDefs(self):
        """
        """
        defs = self._defs
        if not defs:
            return

        self._log(0, '_applyDefs', f'Applying defs: {defs}')

        subtypes = defs.get('subtypes')
        if subtypes:
            self._multiTyped = True
            self._log(0, 'updateDefs', f'_multiTyped enabled')

            # Cast the subtypes to dtype objects
            for sub in subtypes:
                sub.dtype = getType(sub.dtype)
        else:
            dtype = getType(defs.get('dtype', 'any'))
            if dtype != self._dtype:
                self._dtype = dtype
                self._log(0, '_applyDefs', f'New dtype: {self._dtype}')


    def getValue(self):
        """
        Retrieves the value of this object. This will fallback to a default value if
        the current value is Null. Otherwise, attempt to interpolate the value and then
        coerce it into the expected dtype. This is executed each time the Var's value
        is accessed so that it can dynamically generate the correct value.

        Returns
        -------
        self._data : any
            The internal data value
        """
        # Try to rebuild defs every call to stay up to date
        # self._buildDefs()

        if self._missing and self._data is Null:
            self._data = self._defs.get('default', Null)

            # Track that this value is the default value
            self._isDefault = True

        # Apply interpolation to strings
        if self._interpolate and isinstance(self._data, str):
            log  = partial(self._log, 1, 'interpolate')
            data = interpolate(self._data, self, print=log, relativity=self._relativity)

            # The interpolated value was another Sect, replace this Var
            if isSectType(data, ['dict', 'list']):
                # print('Interpolated return was a Sect type, replacing self')
                # self._parent[self._key] = self._data
                # return self._parent[self._key]
                self._log(1, 'getValue', 'Interpolated return was a Sect type, ignoring result to avoid recursion')
                return self._data

            # Interpolation failed, prevent subsequent calls from attempting
            # if data == self._data:
            #     print('Interpolated return was the same, disabling interpolation for this Var')
            #     self._interpolate = False
            #     self._data = Null
            #     return self._data

            self._data = data

        # Switch the subtype if it's defined
        if self._multiTyped:
            self._switchSubtype(self._data)

        # Attempt to coerce this value to the expected dtype
        if self._coerce and not self._dtype.istype(self._data):
            try:
                original = type(self._data)
                new = self._dtype.cast(self._data)
                if new is not self._data:
                    self._data = new
                    self._log(1, 'getValue', f'Coerced from type {original} to {type(new)}')
            except:
                self._log(1, 'getValue', f'Failed to coerce value from {type(self._data)} to {self._dtype.dtype} with value: {self._data!r}')

        if self._convertSlashes and self._data == '\\':
            self._data = Null
            self._log(1, 'getValue', f'Converted backslash to Null')

            if self._nullsEqMissing:
                self._log(1, 'getValue', f'_nullsEqMissing enabled, setting _missing = True')
                self._missing = True

                # Call getValue again to retrieve a default value and possibly interpolation
                return self.getValue()

        return self._NullOrNone(self._data)


    def overrideKey(self, path, value):
        """
        Overrides the value of this Var

        Parameters
        ----------
        path : str
            Unused
        value : any
            Value to set
        """
        self._log(0, 'overrideKey', f'Overriding _data with: {value!r}')
        self._original = self._data
        self._data = value


    def toPrim(self, **kwargs):
        """
        Return as a primitive value

        Returns
        -------
        self.getValue()
        """
        return self.getValue()


    def toYaml(self, tags=[], blacklist=False, nulls=True, **kwargs):
        """
        Converts this object to YAML

        Parameters
        ----------
        tags : list
            List of tags to include in the output. This acts as a whitelist where all
            other tags will be excluded
        blacklist : bool
            All tags in the `tags` parameter will be blacklisted instead, where tags
            not in this list will be accepted
        nulls : bool, default=True
            Include Vars that return Null. Set False to exclude these
        """
        if tags:
            hasTags = self._hasTags(tags)
            if blacklist:
                if hasTags:
                    return []
            elif not hasTags:
                return []

        value = self.getValue()

        if not nulls and value is Null:
            return []

        if isSectType(self._parent, 'list'):
            line = f'- {self._dtype.yaml(self.getValue())}'

        elif isSectType(self._parent, 'dict'):
            line = f'{self._key}: {self._dtype.yaml(self.getValue())}'

        else:
            self._log('e', 'toYaml', 'Calling toYaml on a Var with no parent is not supported')
            return []

        flag  = '*' if self._defs.get('required') else ' '
        dtype = self._dtype.label
        desc  = self._defs.get('sdesc', '')

        return [[line, flag, dtype, desc]]


    def updateChildren(self):
        """
        No children, do nothing
        """
        pass


    def validateObj(self, value=Null, strict=False, checkDefault=False, **kwargs):
        """
        Validates this Var per the defs

        Parameters
        ----------
        value : any, default=Null
            The value to validate. If not provided, uses self.getValue()
        strict : bool, default=False
            Enables strict mode which will run the checks even when the Var is missing
        checkDefault : bool, default=False
            Enables running checks against the default value

        Returns
        -------
        errors : ErrorsDict
            Errors that may have occurred. This dict comes with a `.reduce()` function
            to simplify the errors
        """
        if value is Null:
            value = self.getValue()
        else:
            self._tmpVal = value

        self._log(0, 'validate', 'Validating')
        errors = ErrorsDict()

        if self._skipValidate:
            self._log(0, 'validate', '_skipValidate enabled, returning early')
            return errors

        # Don't run any checks if the key was missing
        strict = strict or self._defs.get('strict')
        if self._missing and not strict:
            if self._defs.get('required'):
                errors['required'] = 'This key is required to be manually set in the config'
            self._log(0, 'validate', f'This Var is missing and not strict')
            return errors

        # Don't run checks if the value is just the default value
        if not checkDefault and self._isDefault:
            self._log(0, 'validate', f'Using default value, skipping checks')
            return errors

        if not self._dtype.istype(value):
            errors['type'] = f'Wrong type: Expected {self._dtype.label!r}, got {type(value)}'

        for check in self._defs.get('checks', []):
            args   = []
            kwargs = {}

            if isSectType(check, 'dict'):
                (check, args), = check.items()
                if isSectType(args, 'dict'):
                    kwargs = args
                    args = []

            self._log(0, 'validate', f'Running check {check}(args={args}, kwargs={kwargs})')
            errors[check] = getRegister(check)(self, *args, **kwargs)

        # Reset at the end
        self._tmpVal = Null

        return errors


    def _switchSubtype(self, value):
        """
        Switches the defs to a different subtype

        Parameters
        ----------
        value : any
            Retrieves the dtype of this value to match to some subtype
        """
        self._log(1, '_switchSubtype', f'Attempting to switch subtype to type {type(value)}')

        for sub in self._defs.subtypes:
            if sub.dtype.istype(value):
                self._log(1, '_switchSubtype', f'Matched to {sub}')
                self._defs |= sub
                self._dtype = sub.dtype
                break
