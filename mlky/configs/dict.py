"""
"""
import logging

from .base   import BaseSect, isSectType
from .null   import Null
from ..utils import printTable


Logger = logging.getLogger('mlky/dict')


class DictSect(BaseSect):
    """
    Dictionary Section
    """
    _logger = Logger
    _dtype  = 'dict'
    _label  = 'D'
    _data   = {}
    _patch  = None

    def _subinit(self, _data={}, _patch=None, **kwargs):
        """
        """
        for key, value in _data.items():
            # Skip reserved keys
            if key in self.__dict__:
                continue

            self._data[key] = self._makeObj(key, value)

        patch = self.parsePatch(_patch)
        if patch:
            self._patch = patch

            # Extract current data
            data = self._data

            # Set self to new base
            self._data = self[patch[0]]._data

            # Update the base names
            for key, obj in self._data.items():
                obj.updateChild(self, key)

            # Patch the base accordingly
            if len(patch) > 1:
                for key in patch[1:]:
                    if key in data:
                        self.applyPatch(data[key])


    def __iter__(self):
        return iter(self._data)


    def _addData(self, key, value):
        """
        Adds a new item to _data

        Parameters
        ----------
        key : str
            Key to set
        value : any
            Value to add
        """
        self._log(1, '_addData', f'Adding key {key!r}: {value}')
        self._data[key] = value


    def _applyDefs(self):
        """
        Applies the defs to this object.
        """
        defs = self._defs
        if not defs:
            return

        self._log(0, '_applyDefs', f'Applying defs: {defs}')

        for key, subdefs in defs.items():
            if key.startswith('.'):
                child = key[1:]
                dtype = subdefs.get('dtype')
                if dtype is None:
                    raise AttributeError(f'The dtype must be defined for every key in the defs, missing for: {key}')

                # Instantiate the child
                if child not in self:
                    value = Null
                    if dtype == 'dict':
                        value = {}
                    elif dtype == 'list':
                        value = []

                    self._log(0, '_applyDefs', f'Creating child {child!r}, dtype: {dtype}')
                    self[child] = value
                    self.get(child, var=True)._missing = True

        self._log(0, '_applyDefs', f'Building children defs')
        for child in self._getChildren():
            child._buildDefs()


    def _getChildren(self):
        """
        Retrieves the children of this object as SectTypes
        """
        return self.values(var=True)


    def applyPatch(self, patch, inplace=True):
        """
        Patches this DictType with another compatible patch object.

        Parameters
        ----------
        patch : dict, DictSect
            Object to patch this object with
        inplace : bool, default=True
            Patch this object inplace. If False, creates a deepcopy and patches that

        Returns
        -------
        DictSect
            Patched object
        """
        if not inplace:
            self = self.deepCopy()
            self._log(0, 'applyPatch', 'Patching on deep copy')

        self._log(0, 'applyPatch', f'Patching with: {patch}')

        if not self.patchCompatible(patch):
            raise AttributeError('Patching object must be a dict type')

        if isSectType(patch, 'dict'):
            self._log(1, 'applyPatch', f'Patching type: DictSect')
            iterable = patch.items(var=True)
        elif self.patchCompatible(patch):
            self._log(1, 'applyPatch', f'Patching type: dict')
            iterable = patch.items()
        else:
            raise AttributeError('Patching object must be a dict type')

        for key, other in iterable:
            # Existing key
            if key in self:
                this = self.get(key, var=True)

                # Check if we can patch this with other
                if this.patchCompatible(other):
                    self._log(1, 'applyPatch', f'Patching child {key!r} with {other}')
                    this.applyPatch(other)
                else:
                    self._log(1, 'applyPatch', f'Replacing child {key!r} with {other}')
                    self[key] = other
            else:
                self._log(1, 'applyPatch', f'Creating child {key!r} with {other}')
                self[key] = other

        return self


    def keys(self):
        return self._data.keys()


    def items(self, var=False):
        return self.toDict(var).items()


    def patchCompatible(self, item):
        """
        Checks if another object is patch compatible with this object
        """
        return isSectType(item, 'dict') or isinstance(item, dict)


    def toDict(self, var=False, recursive=False):
        """
        Converts this object to a dict object

        Parameters
        ----------
        var : bool, default=False
            Return Var objects instead of their values
        recursive : bool, default=False
            Recursively convert children to their primitive value

        Returns
        -------
        data : dict
            dict form of this object
        """
        self._log(0, 'toDict', 'Casting to dict')
        data = {}
        for key, child in self._data.items():
            if not var and isSectType(child, 'var'):
                data[key] = child.getValue()
            elif recursive:
                data[key] = child.toPrim(recursive=recursive)
            else:
                data[key] = child

        return data


    def toPrim(self, *args, **kwargs):
        """
        Passthrough function for toDict()
        """
        self._log(0, 'toPrim', 'Casting to primitive')
        return self.toDict(*args, **kwargs)


    def updateChildren(self):
        """
        Updates child objects with their expected key and this object as the parent
        """
        for key, child in self.items(var=True):
            self._log(0, 'updateChildren', f'Updating child {key}')
            child.updateChild(parent=self, key=key)


    def updateDefs(self):
        """
        Updates the defs for this object by parsing the parent's defs and retrieving
        the appropriate rules
        """
        # Root object doesn't have a parent
        if self._parent is None:
            parentDefs = self._defs
        else:
            parentDefs = self._parent._defs

        defs = parentDefs
        if self._key:
            key  = f'.{self._key}'
            defs = parentDefs.get(key, {})

        for item in defs.get('items', []):
            if item['key'] == '*':
                self._log(0, 'updateDefs', f'Matched * item defs: {item}')
                defs = defs | item
            else:
                self._log(0, 'updateDefs', f"Checking if self has {item['key']} == {item['value']}")
                if self[item['key']] == item['value']:
                    self._log(0, 'updateDefs', f'Matched for item defs: {item}')
                    defs = defs | item

        self._log(0, 'updateDefs', f'Updating defs with: {defs}')

        # Bypass __setattr__ to prevent recursion
        self.__dict__['_defs'] = defs

        for key, subdefs in defs.items():
            if key.startswith('.'):
                child = key[1:]
                dtype = subdefs.get('dtype')
                if dtype is None:
                    raise AttributeError(f'The dtype must be defined for every key in the defs, missing for: {key}')

                # Instantiate the child
                if child not in self:
                    value = Null
                    if dtype == 'dict':
                        value = {}
                    elif dtype == 'list':
                        value = []

                    self._log(0, 'updateDefs', f'Creating child {child!r}, dtype: {dtype}')
                    self[child] = value
                    self.get(child, var=True)._missing = True


    def values(self, var=False):
        return self.toDict(var).values()
