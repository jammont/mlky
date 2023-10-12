"""
Pretty prints slice objects
"""


class PrettySlice:
    """
    Simply pretty prints slices as '{start}:{stop}'

    Acts/is a slice object otherwise
    """
    def __init__(self, *args, **kwargs):
        self._slice = slice(*args, **kwargs)

    def __getattribute__(self, key):
        if key == '_slice':
            return super().__getattribute__('_slice')
        return getattr(self._slice, key)

    def __repr__(self):
        r = ':'
        if self.start is not None:
            r = str(self.start) + r
        if self.stop is not None:
            r += str(self.stop)
        return r
