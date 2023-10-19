"""
Configuration
"""
import json
import logging
import os

from pathlib import Path

import yaml

from . import Sect


Logger = logging.getLogger(__file__)


class Config(Sect):
    def __init__(self, data={}, patch=[], defs={}, debug=-1, validate=True, _raise=True, **kwargs):
        """
        """
        # Config-specific private variables
        self.__dict__['_patch'] = patch = self.parsePatch(patch)
        self.__dict__['_raise'] = _raise

        # If patching, don't apply defs with creation
        if patch:
            # Patching the post initialized state is easiest
            super().__init__(data=data, debug=debug, **kwargs)
            self.patchSects(patch, inplace=True)

            # Apply defs post patching
            self.applyDefinition(defs)
        else:
            super().__init__(
                data  = data,
                defs  = defs,
                debug = debug,
                **kwargs
            )

    def __call__(self, data=None, patch=[], defs={}, *, local=False, **kwargs):
        """
        Enables resetting the global instance Config or create local copies
        """
        # Changing debug state needs to update before anything else to ensure expected behaviour
        debug = kwargs.get('debug')
        if debug is not None:
            if isinstance(debug, int):
                debug = range(0, debug+1)
            self.__dict__['_dbug'] = set(debug)

        # Backwards compatible config = Config()
        if data is None:
            if local is True:
                self._debug(1, '__call__', 'No data, local True, creating deep copy of global instance')
                self = self.deepCopy()
            else:
                self._debug(1, '__call__', 'No data, local False, returning global instance')
            return self

        # First parse the input data from one of the many supported types
        data = self.loadDict(data)

        # Local creates a new instance
        if local:
            self._debug(1, '__call__', 'Creating new local instance of Config using different data')
            self = type(self)(data, patch, defs, **kwargs)
        else:
            # Otherwise update the global instance
            self._debug(1, '__call__', 'Reinitializing the global instance using new data')
            self.__init__(data, patch, defs, **kwargs)
            self._debug(1, '__call__', 'The global instance has been reinitialized')
        return self

    def patchSects(self, keys, inplace=False):
        """
        Patches child Sects in order given

        Parameters
        ----------
        keys: list
            Patch keys list in order
        inplace: bool, default=False
            Auto set the Config `_sect` to the patched Sect

        Returns
        -------
        self: mlky.Config or new: mlky.Sect
            If inplace, returns self with newly set _sect. Otherwise return the
            newly patched Sect
        """
        self._debug(0, 'patchSects', f'Patching using: {keys}')

        new = Sect(debug=self._dbug)
        for key in keys:
            self._debug(0, 'patchSects', f'Patching with [{key!r}]')
            if key in self:
                data = self.get(key, var=True)
                if isinstance(data, Sect):
                    new |= data
                else:
                    Logger.error(f'Key [{key!r}] is not a Sect, it is type {type(data)}')
            else:
                Logger.error(f'Key [{key!r}] is not in this Config')

        if inplace:
            self._debug(0, 'patchSects', f'Setting new patched Sect inplace')
            self.__dict__['_sect'] = new
            new = self

        # Reset all Vars to refresh any magic changes that need to happen
        new.resetVars()

        return new

    def resetSects(self, keys=None, inplace=False, **kwargs):
        """
        Resets to the last initialized state. This is a hard reset, any changes
        to the config since last initialization will be lost. This is because
        this just recreates the Config using the internal `_data` which was the
        last input to Config. Changes to the Config afterwards is done to the
        internal `_sect` and won't be reflected in `_data`.

        Parameters
        ----------
        keys: list, default=None
            Patch keys list. `None` defaults to the last used. Empty list `[]`
            will remove patching altogether
        inplace: bool, default=False
            If true, reset the global instance. If false, reset as a local
            instance. Can also pass local=bool, equivalent to __call__'s local

        Returns
        -------
        Config: mlky.Config
            Reset Config instance, either global or local
        """
        self._debug(0, 'resetSects', 'This is a hard reset, be careful')
        parms = dict(
            data  = self._data,
            patch = self._patch if keys is None else keys,
            local = not inplace,
            defs  = self._defs
        )
        return self(**(parms | kwargs))

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

        dtypes.append('yaml')
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

    @staticmethod
    def parsePatch(patch):
        """
        Supports different patching syntax styles:
            str : "key1<-key2<-keyN"
            list: [key1, key2, keyN]
        """
        if isinstance(patch, str):
            return patch.split('<-')
        return patch


# Transforms the module into a Singleton-like instance
Config = Config()
