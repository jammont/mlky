"""
Date: October, 2022
"""
import argparse
import copy
import logging
import os
import re
import yaml

from . import (
    Functions,
    generate,
    Section,
    Null,
    register
)
from ..utils import (
    column_fmt,
    load_string
)


Logger = logging.getLogger('mlky/config')


class Config:
    """
    Config class

    Notes
    -----
    > How does this work? What's the difference between a class and local instance?
    At run time, Python goes through the scripts and loads all of the code into memory.
    All variable, function, and object definitions are loaded into memory as their own
    independent objects/definitions. When a function is called, the instance of that
    function in memory is called. Same with objects: when a new object is being created,
    Python returns a copy of the definition object. This class modifies the definition
    object directly so that every new instantiation of the class copies the newest
    definition of the object.

    This is defined as the class instance. There is only ever one class definition, and
    therefore only one class instance to copy. All copies of the class instance reference
    the same attributes in memory. Thus, changing the values in one class instance will
    change the values in the other class instances.

    A local instance is the traditional definition of a class instantiation in Python.
    Normally, a class instance is copied but to a new slot in memory. The local instance's
    attributes are their own objects in memory, so accessing them will not affect the class
    instance's attributes.

    Known Issues
    ------------
    * Reloading the module inside an active interpreter (command line, Jupyter) will
    reset the class definition, therefore resetting the class instance. This will cause
    a maximum recursion error. This can be resolved by simply initializing the Config
    class instance again.
    """
    def __init__(self, input=None, inherit=[], local=False, defs={}, defs_inherit=[], _validate=True, _raise=True):
        """
        Parameters
        ----------
        input: tuple, dict, str, defaults=None
            Input of a variety of types:
            - tuple: When reinstantiating from unpickling
            - dict : Instantiating from an in-memory dictionary
            - str  : Either a path to a support file type or is yaml parsable
            - None : Skips instantiation and uses the current class instance
        inherit: list, str, defaults=[]
            - list: Order of keys to apply inheritance
            - str : List of section names split by '<-' in inheritance order
        local: bool, defaults=False
            Enables returning as a local instance object rather than the default class instance
        defs: tuple, dict, str, defaults=None
            Accepts same types as `input`, this is a dictionary defining the requirements for a valid configuration
        defs_inherit: list, defaults=[]
            Order of keys to apply inheritance to definitions dictionary
        _validate: bool, defaults=True
            Executes validation after initialization
        _raise: bool, defaults=True
            Enables raising an exception when validation fails
        """
        # Not local and no input, return the singleton
        if not local and input is None:
            # if not hasattr(Config, '_data'):
            #     raise ValueError('mlky.Config must be initialized with a configuration before creating instances')
            return

        data = None
        name = None

        # Returning from pickle case (__reduce__)
        if isinstance(input, tuple):
            data, input, inherit, defs, local = input
            name = '<-'.join(inherit)
        elif input is not None:
            if isinstance(input, dict):
                data = input

            elif isinstance(input, str):
                data = load_string(input)

            # Apply config-defined inheritances
            for key, value in data.items():
                if isinstance(value, dict) and '^inherit' in value:
                    _inherit = value['^inherit']
                    if isinstance(_inherit, str):
                        _inherit = _inherit.split('<-')
                    _inherit += [key]
                    # Create a deep copy of the keys needed
                    data[key] = self.inherit_(_inherit,
                        copy.deepcopy({k: v for k, v in data.items() if k in _inherit})
                    )

            # Apply inheritance if this isn't returning from pickle
            if inherit:
                if isinstance(inherit, str):
                    inherit = inherit.split('<-')

                data = self.inherit_(inherit, data)
                name = '<-'.join(inherit)

        # Load the requirements if provided
        if defs:
            if isinstance(defs, str):
                defs = load_string(defs)

            if defs_inherit:
                defs = self.inherit_(defs_inherit, defs)

        # Local instances will copy class._data when not provided new input
        if data is None:
            data = self._data

            # Only retrieve _defs when data is None
            if not defs:
                defs = self._defs

        sect = Section(name='', data=data, defs=defs)
        defs = Section(name='', data=defs)

        # Local instance needs to call super() to avoid recursive error due to custom __getattr__
        if local:
            super().__setattr__('_local'  , local  )
            super().__setattr__('_input'  , input  )
            super().__setattr__('_data'   , data   )
            super().__setattr__('_defs'   , defs   )
            super().__setattr__('_sect'   , sect   )
            super().__setattr__('_inherit', inherit)
            super().__setattr__('_name'   , name   )

        # Not a local instance, update the class's attributes
        else:
            self.__class__._local   = False
            self.__class__._input   = input
            self.__class__._data    = data
            self.__class__._defs    = defs
            self.__class__._sect    = sect
            self.__class__._inherit = inherit
            self.__class__._name    = name

        # Done after object initialization so reference keys are available
        sect.replace_()

        # Only validate when a definitions object has been provided
        if _validate:
            if self._defs:
                self.validate_(_raise=_raise)

    def __reduce__(self):
        data = (self._data, self._input, self._inherit, self._defs, self._local)
        return self.__class__, (data, )

    def __contains__(self, key):
        return key in self._sect

    def __iter__(self):
        return iter(self._sect)

    def __len__(self):
        return len(self._sect)

    def __delattr__(self, key):
        del self._sect[key]

    def __delitem__(self, key):
        del self._sect[key]

    def __getattr__(self, key):
        return self._sect[key]

    def __getitem__(self, key):
        return self._sect[key]

    def __setattr__(self, key, value):
        if isinstance(value, Section):
            value._name = key
        self._sect[key] = value

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __repr__(self):
        return f'<Config (local={self._local}, inherit={self._name}, {self._sect})>'

    def get(self, key, other=None, **kwargs):
        return self._sect.get(key, other, **kwargs)

    def items(self):
        return self._sect.items()

    def reset_(self, inherit=None):
        """
        Resets this instance of the Config.
        If class instance, resets class instance.
        If local instance, resets local instance.

        Parameters
        ----------
        inherit: list or str, defaults=None
            Changes behaviour depending on type:
            - None: Reapplies the current inheritance
            - list: Applies inheritance in the provided order
            - str : Reapplies the original inheritance order but changes the last section with this str
        """
        if inherit is None:
            inherit = self._inherit
        if isinstance(inherit, str):
            inherit = [*self._inherit[:-1], inherit]

        # Simply reinitialize
        self.__init__(
            input   = self._input,
            inherit = inherit,
            local   = self._local
        )

    def validate_(self=None, sect=None, defs=None, _raise=True):
        """
        Parameters
        ----------
        sect: dict
            The configuration data
        defs: dict
            The definitions for the configuration
        _raise: bool
            Raises an exception after printing the errors

        Returns
        -------
        errors: dict
            Dictionary of validation results for the given data
        """
        if defs is None:
            defs = self._defs

        if sect is None:
            sect = self._sect

        Logger.info('Checking configuration for errors')
        errors = sect.report_()
        if errors:
            Logger.error('Failed checks, see above for errors')
            if _raise:
                raise Exception('The configuration did not pass validation. See logs for more details.')

        return errors

    def template_(self=None, defs=None, **kwargs):
        """
        Convenience method to call mlky.generate_template from the config object

        Parameters
        ----------
        self: object, default=None
            Normally provided by the object instance. Setting to None allows the
            function to be used as a staticmethod without being such.
        defs: mlky.Section, default=None
            The requirements Section object. If not provided, uses self._defs

        Returns
        -------
        lines: list
            List of strings per line for the YAML template
        """
        return generate(defs or self._defs, **kwargs)

    @staticmethod
    def inherit_(keys, data):
        """
        Deep updates dictionaries in order of inheritance.

        Parameters
        ----------
        keys: list
            List of keys in `data` to apply inheritance in order.
            Example: keys [a, b, c] will apply inheritance a<-b<-c
        data: dict
            Configuration data dictionary

        Returns
        -------
        new: dict
            A new dictionary with the inheritance order applied
        """
        def update(a, b):
            """
            Recursively updates the dictionary B with the data of dictionary A
            """
            for k, v in a.items():
                if k in b and isinstance(v, dict):
                    update(v, b[k])
                else:
                    b[k] = v

            return b

        new = {}
        for key in keys:
            if key not in data:
                Logger.warning(f'Key {key!r} not in {data.keys()}')
                continue

            new = update(data[key], new)

        return new


@register('config.replace')
def replace(value):
    """
    Replaces format signals in strings with values from the config relative to
    its inheritance structure.

    Parameters
    ----------
    value: str
        Matches roughly to ${config.*} in the string and replaces them with the
        corrosponding config value. See notes the regex for accuracy.

    Returns
    -------
    string: str
        Same string but with the values replaced.

    Notes
    -----
    The regex used for matching is r"\${([\.\$].*?)}". This will match to any
    string starting with `.` or `$` wrapped by `${}`. Reasons to only match
    starting with specific keys is to:
        - `.` - Config value lookup
        - `$` - Environment variable lookup

    Config references must be relative to the inheritance structure. With
    inheritance, the top level sections do not exist. Without inheritance, they
    do. Examples:

    >>> # Without inheritance
    >>> config = Config('''
    default:
        path: /abc
        vars:
            x: 1
            y: 2
    foo:
        file: ${.default.path}/${.default.vars.x}/${.default.vars.y}
    ''')
    >>> replace(config.foo.file)
    '/abc/1/2'

    >>> # With inheritance
    >>> config = Config('''
    default:
        path: /abc
        vars:
            x: 1
            y: 2
    foo:
        file: ${.path}/${.vars.x}/${.vars.y}
    ''', 'default<-foo')
    >>> replace(config.file)
    '/abc/1/2'
    """
    matches = re.findall(r"\${([\.\$\!].*?)}", value)

    for match in matches:
        # Config lookup case
        if match.startswith('.'):
            keys = match.split('.')

            if len(keys) < 2:
                Logger.error(f'Keys path provided is invalid, returning without replacement: {keys!r}')
                return value

            data = Config()
            for key in keys[1:]:
                data = data.__getattr__(key)

            if isinstance(data, Null):
                Logger.warning(f'Lookup({match}) returned Null. This may not be expected and may cause issues.')

        # Environment variable lookup case
        elif match.startswith('$'):
            data = Functions.check('get_env', match[1:])

        # Lookup custom function case
        elif match.startswith('?'):
            data = Functions.check(match[1:])

        # Data lookup case
        elif match.startswith('!'):
            return Functions.check(match[1:])

        else:
            Logger.warning(f'Replacement matched to string but no valid starter token provided: {match!r}')

        value = value.replace('${'+ match +'}', str(data))

    return value
