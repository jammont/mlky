"""
The main configuration class of mlky

The primary features of this class are:
    1. Manage the patching of top-level sections
    2. Act as a Singleton-like instance

Beyond that, Config is simply a Sect object
"""
import logging

import yaml

from . import (
    funcs,
    NullDict,
    Sect
)


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

            if defs:
                # Apply defs post patching
                self.applyDefinition(defs)
        else:
            super().__init__(
                data  = data,
                defs  = defs,
                debug = debug,
                **kwargs
            )

        # Always called after initialization in case registered checks need to be re-added
        funcs.getRegister('config.addChecks')()

        # Reset all Vars to refresh any magic changes that need to happen
        self.resetVars()

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
                self._log(1, '__call__', 'No data, local True, creating deep copy of global instance')
                self = self.deepCopy()
                self._log(1, '__call__', 'Returning deep copy')
            else:
                self._log(1, '__call__', 'No data, local False, returning global instance')
            return self

        # Local creates a new instance
        if local:
            self._log(1, '__call__', 'Creating new local instance of Config using different data')
            self = type(self)(data, patch, defs, **kwargs)
            self._log(1, '__call__', 'Returning new, different local instance')
        else:
            # Otherwise update the global instance
            self._log(1, '__call__', 'Reinitializing the global instance using new data')
            self.__init__(data, patch, defs, **kwargs)
            self._log(1, '__call__', 'The global instance has been reinitialized')
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
        self._log(0, 'patchSects', f'Patching using: {keys}')

        new = Sect(debug=self._dbug)
        for key in keys:
            self._log(0, 'patchSects', f'Patching with [{key!r}]')
            if key in self:
                data = self.get(key, var=True)
                if isinstance(data, Sect):
                    new |= data
                else:
                    Logger.error(f'Key [{key!r}] is not a Sect, it is type {type(data)}')
            else:
                Logger.error(f'Key [{key!r}] is not in this Config')

        if inplace:
            self._log(0, 'patchSects', f'Setting new patched Sect inplace')
            self.__dict__['_sect'] = NullDict(new.toPrimitive(deep=False, var=True))
            new = self

        return new

    def resetSects(self, keys=None, **kwargs):
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

        Returns
        -------
        Config: mlky.Config
            Reset Config instance, either global or local
        """
        self._log(0, 'resetSects', 'This is a hard reset, be careful')
        parms = dict(
            data  = self._data,
            patch = self._patch if keys is None else keys,
            defs  = self._defs or {}
        )
        return self(**(parms | kwargs))

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

    @staticmethod
    def addChecks():
        """
        Simply calls funcs.getRegister('config.addChecks')()
        """
        funcs.getRegister('config.addChecks')()


# Transforms the module into a Singleton-like instance
GlobalConfig = Config()
