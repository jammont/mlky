"""
"""
import os
import pickle
import yaml


def column_fmt(iterable, enum=False, delimiter='=', offset=1, prepend='', print=print, columns={}, _i=0):
    """
    Parameters can be set on a per column basis using the columns parameter. This is a
    dictionary of column indices as keys and the parameters for that column as the
    value.

    Parameters
    ----------
    iterable: iterable
        Any iterable consisting of subscriptable iterables of strings
    enum: bool, default=False
        Whether to include enumeration of the items
    delimiter, default='='
        The symbol to use between the key and the value
    offset: int, default=1
        Space between the key and the delimiter: {key}{offset}{delimiter}
        Defaults to 1, eg: "key ="
    prepend: str, default=''
        Any string to prepend to each line
    print: func, default=print
        The print function to use. Allows using custom function instead of Python's normal print
    columns: dict, default={}
        Arguments for each column. Only the delimiter and offset may be different
        between columns. The keys for this are the column number starting from 0
    _i: int, default=0
        Which column is being formatted. Used to retrieve column-specific arguments

    Returns
    -------
    formatted: list
    """
    # Retrieve the parameters for this column
    args      = columns.get(_i, {})
    delimiter = args.get('delimiter', delimiter)
    offset    = args.get('offset'   , offset   )

    # Left and right side of the delimiter for this column
    left  = []
    right = []
    for item in iterable:
        if len(item) > 1:
            left.append(str(item[0]))
            right.append(str(item[1]))

    if not left:
        return []

    padding   = max([0, max(map(len, left))]) + offset
    formatter = prepend
    if enum:
        formatter += '{i:' + f'{len(str(len(iterable)))}' + '}: '
    formatter += '{left:'+ str(padding) + '}' + delimiter + ' {right}'

    i = 0
    formatted = []
    for item in iterable:
        if len(item) > 1:
            string = formatter.format(i=i, left=left[i], right=right[i])
            if len(item) > 2:
                formatted.append((string, *item[2:]))
            else:
                formatted.append((string, ))
            i += 1
        else:
            formatted.append(item)

    # Check if there are any more columns to format
    if any([len(item) > 1 for item in formatted]):
        # Only delimiter and offset are carried forward, other parameters disabled
        formatted = column_fmt(formatted,
            delimiter = delimiter,
            offset    = offset,
            enum      = False,
            prepend   = '',
            print     = None,
            columns   = columns,
            _i        = _i + 1
        )

    # Reduce from [(str,), (str,), ...] to [str, str, ...]
    if _i == 0:
        formatted = [item for [item] in formatted]

    # Print is only set on the first call
    if print:
        for item in formatted:
            print(item)

    return formatted

def align_print(iterable, enum=False, delimiter='=', offset=1, prepend='', print=print):
    """
    Pretty prints an iterable in the form {key} = {value} such that the delimiter (=)
    aligns on each line

    Parameters
    ----------
    iterable: iterable
        Any iterable with a .items() function
    enum: bool, default = False
        Whether to include enumeration of the items
    delimiter, default = '='
        The symbol to use between the key and the value
    offset: int, default = 1
        Space between the key and the delimiter: {key}{offset}{delimiter}
        Defaults to 1, eg: "key ="
    prepend: str, default = ''
        Any string to prepend to each line
    print: func, default = print
        The print function to use. Allows using custom function instead of Python's normal print
    """
    if hasattr(iterable, 'items'):
        pad   = len(max(iterable.keys(), key=len))
        items = iterable.items()
    else:
        assert len(iterable) > 0, 'Iterable must not be empty'
        assert all([len(item) == 2 for item in iterable]), 'Iterable must contain iterables of length 2'
        pad   = len(max(iterable, key=lambda v: len(v[0])))
        items = iterable

    # Determine how much padding between the key and delimiter
    pad = max([1, pad]) + offset

    # Build the formatted string
    fmt = prepend
    if enum:
        fmt += '- {i:' + f'{len(str(len(iterable)))}' + '}: '
    fmt += '{key:'+ str(pad) + '}' + delimiter + ' {value}'

    # Create the formatted list
    fmt_list = []
    for i, (key, value) in enumerate(items):
        string = fmt.format(i=i, key=key, value=value)
        fmt_list.append(string)

    for string in fmt_list:
        print(string)

    return fmt_list

def mkdir(path):
    """
    Attempts to create directories for a given path
    """
    # Make sure this is a directory path
    path, _ = os.path.split(path)

    # Split into parts to reconstruct
    split = path.split('/')

    # Now reconstruct the path one step at a time and ensure the directory exists
    for i in range(2, len(split)+1):
        dir = '/'.join(split[:i])
        if not os.path.exists(dir):
            try:
                os.mkdir(dir, mode=0o771)
            except Exception as e:
                Logger.exception(f'Failed to create directory {dir}')
                raise e

def load_string(string):
    """
    Loads a dict from a string
    """
    # File case
    if os.path.exists(string):
        with open(string, 'r') as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
    # Raw string case
    else:
        data = yaml.load(string, Loader=yaml.FullLoader)

    return data

def load_pkl(file):
    """
    Loads data from a pickle

    Parameters
    ----------
    file : str
        Path to a Python pickle file to load

    Returns
    -------
    any
        The data object loaded from the pickle file
    """
    return pickle.load(open(file, 'rb'))

def save_pkl(data, output):
    """
    Saves data to a file via pickle

    Parameters
    ----------
    data: any
        Any pickleable object
    output : str
        Path to a file to dump the data to via pickle
    """
    mkdir(output)
    with open(output, 'wb') as file:
        pickle.dump(data, file)

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
