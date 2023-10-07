import logging


from . import Sect

Logger = logging.getLogger('config.py')

import yaml

class utils:
    @staticmethod
    def loadDict(data):
        """
        Loads a dict from
        """
        import os
        # Dicts and Sects return as-is
        if isinstance(data, (dict, Sect, list, tuple)):
            return data
        elif isinstance(data, str):
            # File case
            if os.path.isfile(data):
                _, ext = os.path.splitext(data)
                if ext in ['.yml', '.yaml']:
                    with open(data, 'r') as file:
                        data = yaml.load(file, Loader=yaml.FullLoader)
                elif ext in ['.json']:
                    # TODO: Add json support
                    ...
            # String case
            else:
                try:
                    # Raw yaml strings supported only
                    data = yaml.load(data, Loader=yaml.FullLoader)
                except:
                    raise TypeError('Data input is a string but is not a file nor a yaml string')
            return data
        else:
            raise TypeError(f'Data input is not a supported type, got {type(data)!r} expected one of: [filepath str, dict, Sect, list, tuple, yaml string]')


class Config(Sect):
    def __init__(self, data={}, patch=[], defs={}, patch_defs=[], debug=-1, validate=True, _raise=True, **kwargs):
        """
        """
        super().__init__(
            data  = data,
            defs  = defs,
            debug = debug,
            **kwargs
        )

        # Config-specific private variables
        self.__dict__['_dataPatch'] = patch
        self.__dict__['_defsPatch'] = patch_defs
        self.__dict__['_raise']     = _raise

        # Patch the post-initialized state
        if patch:
            self.patchSects(patch, inplace=True)

    def __call__(self, data=None, patch=[], local=False, **kwargs):
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
                self = self.deepCopy()
                self._debug(1, '__call__', 'No data, local True, creating deep copy of global instance')
            else:
                self._debug(1, '__call__', 'No data, local False, returning global instance')
            return self

        # First parse the input data from one of the many supported types
        data = utils.loadDict(data)

        # Local creates a new instance
        if local:
            self._debug(1, '__call__', 'Creating new local instance of Config using different data')
            self = type(self)(data, patch, **kwargs)
        else:
            # Otherwise update the global instance
            self._debug(1, '__call__', 'Reinitializing the global instance using new data')
            self.__init__(data, patch, **kwargs)
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

        new = Sect(
            debug = self._dbug,
            _repr = self._repr
        )
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
            data       = self._data,
            patch      = self._patch if keys is None else keys,
            local      = not inplace,
            defs       = self._defs,
            patch_defs = self._defsPatch
        )
        return self(**(parms | kwargs))

# Transforms the module into a Singleton-like instance
Config = Config()
