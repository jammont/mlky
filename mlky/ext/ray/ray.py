import logging

from pathlib import Path

import ray

from ray._private.utils import get_ray_temp_dir

from ...configs.dict import DictSect
from ...configs.sect import types


Logger = logging.getLogger('mlky/ext/ray')


class RayDictSect(DictSect):
    _logger = Logger


    def _subinit(self, *args, **kwargs):
        super()._subinit(*args, **kwargs)

        if ray.is_initialized():
            self.initRay()


    def initRay(self):
        path = Path(get_ray_temp_dir()) / 'session_latest'
        path = Path(path.readlink()) / 'mlky.yml'

        # Only occur on the root
        if self._key == '':

            # Attempt to load from an existing session
            if not self._data:
                if path.exists():
                    self(path)
                    self._log(3, '_subinit', f'Loaded from: {path}')

            # Dump this populated object to the tmp session
            else:
                self.toYaml(file=path, header=False)
                self._log(3, '_subinit', f'Dumped to: {path}')


types['dict'] = RayDictSect
