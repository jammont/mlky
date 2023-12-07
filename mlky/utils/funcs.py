"""
Function manipulators
"""


def catch(func):
    """
    Decorator that protects the caller from an exception raised by the called function.

    Parameters
    ----------
    func: function
        The function to wrap

    Returns
    -------
    _wrap: function
        The wrapper function that calls func inside of a try/except block
    """
    def _wrap(*args, **kwargs):
        """
        Wrapper function

        Parameters
        ----------
        *args: list
            List of positional arguments for func
        **kwargs: dict
            Dict of keyword arguments for func
        """
        try:
            func(*args, **kwargs)
        except:
            Logger.exception(f'Function <{func.__name__}> raised an exception')

    # Need to pass the docs on for sphinx to generate properly
    _wrap.__doc__ = func.__doc__
    return _wrap
