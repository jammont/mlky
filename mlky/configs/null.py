"""
The Null class of mlky.
"""

class Null:
    """
    Acts like a Nonetype (generally) without raising an exception in common use
    cases such as:
    - __getattr__, __getitem__ will return itself, preventing raising missing
    attribute. Ex: config.this_key_is_missing.also_missing will return Null.
    - Dict functions .get, .keys, and .items will return empty lists/dicts.
    - Comparisons should always return False unless compared to a None or Null
    type.
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
