"""
"""
import logging

from .base   import BaseSect, isSectType
from .null   import Null
from ..utils import printTable


Logger = logging.getLogger('mlky/list')


class ListSect(BaseSect):
    """
    List Section
    """
    _logger = Logger
    _dtype  = 'list'
    _label  = 'L'
    _data   = []

    # When patching perform via append instead of replacing
    _patchAppend = False # NYI


    def _subinit(self, _data=[], **kwargs):
        """
        """
        for key, value in enumerate(_data):
            self._data.append(self._makeObj(key, value))


    def __iter__(self):
        return iter(self.toList())


    def _addData(self, key, value):
        if key == 'append':
            self._log(1, '_addData', f'Appending index[{key}] = {value}')
            self._data.append(value)
        else:
            self._log(1, '_addData', f'Changing index[{key}] to {value}')
            self._data[key] = value


    def _applyDefs(self):
        defs = self._defs
        if not defs:
            return

        self._log(0, '_applyDefs', f'Applying defs: {defs}')

        for key, subdefs in defs.items():
            # A default value is provided and no data for this object
            if key == 'default' and not(self):
                self._log(0, '_applyDefs', f'Overriding with defs: {subdefs}')
                self._data = subdefs._data

        self._log(0, '_applyDefs', f'Building children defs')
        for child in self._getChildren():
            child._buildDefs()


    def _getChildren(self):
        return self.toList(var=True, recursive=False)


    def append(self, value):
        obj = self._makeObj(len(self._data), value)
        self._addData('append', obj)


    def applyPatch(self, patch, inplace=True):
        """
        WIP - Right now just replaces outright
        """
        if not inplace:
            self = self.deepCopy()
            self._log(0, 'applyPatch', 'Patching on deep copy')

        if not isSectType(patch):
            patch = self._makeObj(patch)

        self._data = patch._data

        self._log(0, 'applyPatch', f'Patching with: {patch}')
        return self


    def patchCompatible(self, item):
        """
        Checks if another object is patch compatible with this object
        """
        return isinstance(item, (type(self), list))


    def toList(self, var=False, recursive=False):
        """
        """
        data = []
        for child in self._data:
            if not var and isSectType(child, 'var'):
                data.append(child.getValue())
            elif recursive:
                data.append(child.toPrim(recursive=recursive))
            else:
                data.append(child)

        return data


    def toPrim(self, var=False, recursive=True):
        """
        Parameters
        ----------
        var: bool, default=False
            Return Var objects instead of their held values
        recursive: bool, default=True
            Recursively convert children to their primitive types as well
        """
        return self.toList(var, recursive)


    def toYaml(self, *args, listStyle='long', **kwargs):
        lines = super().toYaml(*args, **kwargs)

        if listStyle == 'short':
            # Confirm this has children and all are Vars
            if any(self) and all([isSectType(child, 'var') for child in self._getChildren()]):
                values = [line[0].split('- ')[1] for line in lines[1:]]
                lines[0][0] += f" [{', '.join(values)}]"
                del lines[1:]

        return lines


    def updateChildren(self):
        """
        """
        for key, child in enumerate(self.toList(var=True)):
            child.updateChild(parent=self, key=key)


    def updateDefs(self):
        """
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

        self._log(0, 'updateDefs', f'Updating defs with: {defs}')
        self._defs = defs

        for key, subdefs in defs.items():
            if key.startswith('.'):
                child = key[1:]
                dtype = subdefs.get('dtype')
                if dtype is None:
                    raise AttributeError(f'The dtype must be defined for every key in the defs, missing for: {key}')

                if child.isnumeric():
                    self._log(0, 'updateDefs', f'Casting child key to numeric: {child}')
                    child = int(child)
                else:
                    self._log(0, 'updateDefs', f'Child key is non-numeric, changing to append')
                    child = 'append'

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
