"""
"""
import logging

from . import (
    Functions,
    Null
)


Logger = logging.getLogger('mlky/section')


class Var:
    """
    Container class to house variables for Section objects. Section will
    normally return the exact value of this object during runtime. This is used
    under the hood to do facilitate MLky functions such as value lookups and
    type checking / enforcement. To retrieve the Var object from Section, use
    Section.get(key, var=True).
    """
    def __init__(self, name, key, value, missing=False, required=False, type=None, default=Null(), checks=[]):
        """
        """
        if isinstance(checks, dict):
            Logger.warning(f'Checks for {name} is a dict instead of a list, attempting to correct but you may need to fix the definitions document')
            checks = [{k: v} for k, v in checks.items()]

        # Prepend so type checking is the first check ran
        checks = [{'type': {'type': type}}] + checks

        super().__setattr__('name'    , name    )
        super().__setattr__('key'     , key     )
        super().__setattr__('value'   , value   )
        super().__setattr__('missing' , missing )
        super().__setattr__('required', required)
        super().__setattr__('type'    , type    )
        super().__setattr__('default' , default )
        super().__setattr__('checks'  , checks  )

    def __reduce__(self):
        return (type(self), (self.name, self.key, self.value, self.required, self.type, self.default))

    def __setattr__(self, key, value):
        """
        """
        if key == 'value':
            if isinstance(value, str):
                value = self.replace(value)

            if self.validate(value, reduced=True) is not True:
                Logger.error('Changing the value will cause validation to fail. See <This Var>.validate() for errors.')
        elif key == 'type':
            if Functions.check('type', type=value) is not True:
                Logger.warning(f'Changing type from {self.type!r} to {value!r} will cause validation to fail with the current value: {self.value!r}')

            # Replace the check function
            self.checks[0] = {'type': {'type': value}}

        super().__setattr__(key, value)

    def __repr__(self):
        return f'<Var({self.key}={self.value!r})>'

    def check_type(self, value=Null):
        """
        Checks a given value against the type set for this object.
        """
        if value is Null:
            value = self.value

        return Functions.check('type', value, self.type)

    def validate(self, value=Null, reduced=True):
        """
        Parameters
        ----------
        reduced: bool, default=True
            Excludes checks that return True
        """
        if value is Null:
            value = self.value

        errors = {}

        typecheck = []
        if self.missing:
            if self.required:
                errors['required'] = 'This key is required to be manually set in the config'

            # Don't run any checks if the key was missing
            return errors or True

        for check in self.checks:
            kwargs = {}
            if isinstance(check, dict):
                (check, kwargs), = list(check.items())

            errs = Functions.check(check, value, **kwargs)
            if errs is True:
                if not reduced:
                    errors[check] = errs
            else:
                errors[check] = errs

        return errors or True

    def validate_(self, *args, **kwargs):
        """
        Alias for self.validate() to simplify code in Section since Section uses
        Section.validate_().
        """
        return self.validate(*args, **kwargs)

    def get(self):
        if not isinstance(self.value, Null):
            return self.value
        else:
            return self.default

    def replace(self, value=None):
        """
        Importing inside this function breaks the potential import loop, where
        a->b means a depends on b:

           v--- Var <---|
        replace      Section
           |-> Config --^
        """
        # Have to import within function to avoid recursive imports
        from mlky import replace

        def lookup(value):
            replaced = replace(value)
            if value != replaced:
                Logger.debug(f'Updated {self.name} from {value!r} to {replaced!r}')

                return replaced
            return value

        if value is None:
            if isinstance(self.value, str):
                super().__setattr__('value', lookup(self.value))
            elif isinstance(self.value, list):
                super().__setattr__('value', [
                    lookup(item) if isinstance(item, str) else item
                    for item in self.value
                ])
        else:
            return lookup(value)


class Section:
    """
    A section of the Config, essentially acts like a dict with dot notation

    Notes
    -----
    YAML Support:
        - Basic types (int, str, bool)
        - Lists of basic types (not dict)

    Limitations:
        - YAML allows for an infinite depth of nested lists. There are very real
        use cases of needing a list of sections/dicts, but not for more than 1 level deep.
        The Section object will only support lists of dicts 1 level deep. It will not
        support lists of lists of dicts (ie. two+ levels of nesting)
    """
    DEBUG = False

    def __init__(self, data={}, name='', defs={}, missing=False, debug=False, _repr=10):
        """
        Parameters
        ----------
        name: str, defaults=None
        data: dict, defaults={}
        defs: dict, defaults={}
            Definitions dictionary
        missing: bool, defaults=False
            Informs this section that it was missing from the config. This is
            normally passed by the parent Section so that the child can report
            it during validation.
        _repr: int, defaults=10
            How many of each attributes and sections keys to print in the Section.__repr__
        """
        self.__dict__['_name'] = name
        self.__dict__['_data'] = {}
        self.__dict__['_defs'] = defs
        self.__dict__['_miss'] = missing
        self.__dict__['_repr'] = _repr

        children = defs.get('.children', {})
        if isinstance(data, dict):
            for key, value in data.items():
                self.set_data_(key, value, children.get(key, {}))
        elif isinstance(data, (list, tuple)):
            for i, value in enumerate(data):
                self.set_data_(i, value, defs)

        # Populate any missing keys
        for key, value in children.items():
            if key not in data:
                self.set_defs_(key, value)

        if debug:
            self.__class__.DEBUG = debug

    def __call__(self, sect):
        """
        Applies inheritance to this section using the provided section.

        Inheritance is only applied to sections. Therefore, lists of sections
        will be overridden entirely instead of deep inheriting due to undesired
        complexity. If a deep inheritance feature is ever posted to github, this
        can be reconsidered.
        """
        for key, value in sect.items(var=True):
            # Everything in a Section is either a Var or a Section
            if isinstance(value, Var):
                self._data[key] = value
            elif isinstance(value, Section):
                if isinstance(self._data[key], Section):
                    # Apply inheritance
                    self._data[key](value)
                else:
                    self._data[key] = value
            else:
                Logger.error(f'Section has a value that is not a Var or Section: {type(value)} - {value}')

    def set_data_(self, key, value, defs={}):
        """
        Sets keys from a data dictionary
        """
        # Convert dicts to Sections
        if isinstance(value, dict):
            self._data[key] = Section(name=self.fmt_(key), data=value, defs=defs)

        # List of dicts
        elif isinstance(value, (list, tuple)) and all([isinstance(v, dict) for v in value]):
            self._data[key] = [
                Section(name=self.fmt_(key, i), data=item, defs=defs)
                for i, item in enumerate(value)
            ]

        # Key already exists, Var object instantiated
        elif key in self._data:
            self._data[key].value = value

        # Already a Var object, typically from unpickling
        elif isinstance(value, Var):
            self._data[key] = value

        else:
            self._data[key] = Var(
                name     = self.fmt_(key),
                key      = key,
                value    = value,
                required = defs.get('.required', False ),
                type     = defs.get('.type'    , Null  ),
                default  = defs.get('.default' , Null()),
                checks   = defs.get('.checks'  , []    )
            )

    def set_defs_(self, key, defs):
        """
        Sets keys from a definitions dictionary
        """
        if '.children' in defs:
            type = defs.get('.type')
            if type in ('dict', 'sect', 'Section', None):
                self._data[key] = Section(name=self.fmt_(key), data={}, defs=defs, missing=True)

            if type == 'list':
                self._data[key] = [
                    Section(name=self.fmt_(key, i), data={}, defs=defs, missing=True)
                    for i in range(defs.get('.number', 1))
                ]
        else:
            self._data[key] = Var(
                name     = self.fmt_(key),
                key      = key,
                value    = Null(),
                missing  = True,
                required = defs.get('.required', False ),
                type     = defs.get('.type'    , Null  ),
                default  = defs.get('.default' , Null()),
                checks   = defs.get('.checks'  , []    )
            )

    def __reduce__(self):
        return (type(self), (self._name, self._data, self._defs))

    def __deepcopy__(self, memo):
        new = type(self)(self._name)
        memo[id(self)] = new
        new._data = copy.deepcopy(self._data, memo)
        new._defs = copy.deepcopy(self._defs, memo)
        return new

    def __contains__(self, key):
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __getattr__(self, key, var=False):
        if key in self.__dict__:
            return self.__dict__[key]
        elif key in self._data:
            value = self._data[key]
            if isinstance(value, Var):
                if self.__class__.DEBUG or var:
                    return value
                return value.get()
            return value
        return Null()

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __setattr__(self, key, value):
        if key in self.__dict__:
            self.__dict__[key] = value
        else:
            self.set_data_(key, value)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __delattr__(self, key):
        if self.get(key, var=True).required:
            Logger.warning(f'Deleting required key: {key!r}')
        del self._data[key]

    def __delitem__(self, key):
        self.__delattr__(key)

    def __repr__(self):
        attributes, sections = [], []
        for key, value in self.items():
            if isinstance(value, Section):
                sections.append(key)
            else:
                attributes.append(key)

        if len(attributes) > self._repr:
            attributes = f'{attributes[:self._repr]}+[{len(attributes)-self._repr} more]'
        if len(sections) > self._repr:
            sections = f'{sections[:self._repr]}+[{len(sections)-self._repr} more]'

        return f"<Section {self._name or '.'} (attributes={attributes}, sections={sections})>"

    def has_attrs_(self):
        for key, value in self.items():
            if isinstance(value, Var):
                return True
        return False

    def has_sects_(self):
        for key, value in self.items():
            if isinstance(value, Section):
                return True
        return False

    def fmt_(self, key, i=None):
        """
        Formats a key child key with the parent key
        """
        if i is None:
            return f'{self._name}.{key}'
        else:
            return f'{self._name}.{key}[{i}]'

    def replace_(self, value=None):
        """
        """
        if value is None:
            value = self._data.values()

        for item in value:
            if isinstance(item, Var):
                item.replace()
            elif isinstance(item, Section):
                self.replace_(item._data.values())
            elif isinstance(item, dict):
                self.replace_(item.values())
            elif isinstance(item, list):
                self.replace_(item)

    def validate_(self, value=None, reduced=True, fmt=False):
        """
        """
        errors = []

        # If this Section was missing AND it's required, report that
        if self._miss and self._defs.get('.required'):
            error = {'required': 'This section is required to be manually set'}
            errors.append((self._name, error))

        if value is None:
            for key, value in self._data.items():
                if isinstance(value, (Section, Var)):
                    errs = value.validate_(reduced=reduced)
                    if errs is not True:
                        # errors[self.fmt_(key)] = errs
                        errors.append((self.fmt_(key), errs))

                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        # errors[self.fmt_(key, i)] = self.validate_(item, reduced=reduced)
                        errors.append(
                            (self.fmt_(key, i), self.validate_(item, reduced=reduced))
                        )

        if isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(value, (Section, Var)):
                    errs = value.validate_(reduced=reduced)
                    if errs is not True:
                        # errors[self.fmt_(key)] = errs
                        errors.append((self.fmt_(key), errs))

                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        # errors[self.fmt_(key, i)] = self.validate_(item, reduced=reduced)
                        errors.append(
                            (self.fmt_(key, i), self.validate_(item, reduced=reduced))
                        )

        return errors or True

    def report_(self, errors=None):
        """
        Pretty prints a validation dictionary returned by a Section object

        Returns
        -------
        bool
            Returns True if there was an error reported, otherwise returns False
        """
        if errors is None:
            errors = self.validate_()

        error = False
        for key, errs in errors:
            if isinstance(errs, list):
                error = self.report_(errs)
            elif isinstance(errs, dict):
                error = True
                Logger.error(key)
                for name, msgs in errs.items():
                    Logger.error(f'  * {name}')
                    if isinstance(msgs, str):
                        Logger.error(f'    - {msgs}')
                    elif isinstance(msgs, list):
                        for msgs in msgs:
                            Logger.error(f'    - {msgs}')
                    else:
                        Logger.debug(f'A check function returned something other than a list or str: {type(msgs)} - {msgs}')

        return error

    def get(self, key, other=None, **kwargs):
        if key in self._data:
            return self.__getattr__(key, **kwargs)
        return other

    def items(self, var=False):
        return [(key, self.get(key, var=var)) for key in self]

    def keys(self):
        return self._data.keys()
