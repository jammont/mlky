"""
Var objects are containers to hold values of a mlky Sect
"""
import copy
import logging

from . import (
    Functions,
    Null
)


Logger = logging.getLogger(__file__)


class Errors(dict):
    def reduce(self):
        return {k: v for k, v in self.items() if isinstance(v, (str, list))}


class Var:
    def __init__(self, name, key, value=Null, default=Null, dtype=Null, required=False, missing=False, checks=[]):
        """
        Variable container object
        """
        self.name     = name
        self.key      = key
        self.default  = default
        self.dtype    = dtype
        self.required = required
        self.missing  = missing
        self.checks   = checks

        # Assigned differently to circumvent auto-calling validate()
        super().__setattr__('value', value)

    def __eq__(self, other):
        data = self.toDict()
        if isinstance(other, dict):
            return data == other
        elif isinstance(other, self.__class__):
            return data == other.toDict()
        return False

    def __deepcopy__(self, memo):
        data = copy.deepcopy(self.__dict__, memo)
        new  = type(self)(**data)
        memo[id(self)] = new
        return new

    def __reduce__(self):
        return (type(self), (
            self.name, self.key, self.value,
            self.default, self.dtype, self.required,
            self.missing, self.checks
        ))

    def __setattr__(self, key, value):
        """
        """
        if key == 'value':
            # Non-empty dict means errors found
            if self.validate(value).reduce():
                Logger.error(f'Changing the value of this Var({self.name}) will cause validation to fail. See var.validate() for errors.')

        super().__setattr__(key, value)

    def __repr__(self):
        return f'<Var({self.key}={self.value!r})>'

    def toDict(self):
        return self.__dict__

    def deepCopy(self):
        return copy.deepcopy(self)

    def checkType(self, value=Null):
        """
        Checks a given value against the type set for this object.
        """
        if value is Null:
            value = self.value

        # Not required, already a null value (either set in config explicitly as null or was inherently null)
        if not self.required and value is Null:
            return True

        return Functions.check('type', value, self.dtype)

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
        errors = Errors()

        # Don't run any checks if the key was missing
        if self.missing:
            if self.required:
                errors['required'] = 'This key is required to be manually set in the config'
            return errors or True

        # Check the type before anything else
        errors['type'] = self.checkType()

        for check in self.checks:
            kwargs = {}
            if isinstance(check, dict):
                (check, kwargs), = list(check.items())

            errors[check] = Functions.check(check, value, **kwargs)

        return errors or True

    def replace(self):
        """
        TODO
        """
        ...
