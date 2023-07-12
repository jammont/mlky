"""
"""

class Null:
    """
    Acts like a Nonetype (generally) without raising an exception.
    """
    def __call__(self, *args, **kwargs):
        pass

    def __deepcopy__(self, memo):
        return type(self)()

    def __bool__(self):
        return False

    def __eq__(self, other):
        if type(other) in [type(None), type(self)] or other is Null:
            return True
        return False

    def __hash__(self):
        return hash(None)

    def __getattr__(self, key):
        return self

    def __getitem__(self, key):
        return self

    def __contains__(self):
        return False

    def __iter__(self):
        return iter(())

    def __len__(self):
        return 0

    def __repr__(self):
        return 'Null'

    def __str__(self):
        return 'Null'

    def get(self, key, other=None):
        return other

    def keys(self):
        return []

    def items(self):
        return {}
