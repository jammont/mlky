"""
Pretty printers
"""


def printTable(iterable, enum=False, delimiter='=', offset=1, prepend='', truncate=None, print=print, columns={}, _i=0):
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
    delimiter: str, default='='
        The symbol to use between the key and the value
    offset: int, default=1
        Space between the key and the delimiter: {key}{offset}{delimiter}
        Defaults to 1, eg: "key ="
    prepend: str, default=''
        Any string to prepend to each line
    truncate: int, default=None
        Truncates a value to a provided length for prettier printing
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
    truncate  = args.get('truncate' , truncate )

    # Left and right side of the delimiter for this column
    left  = []
    right = []
    for item in iterable:
        if len(item) > 1:
            left.append(str(item[0]))
            right.append(str(item[1]))

    if not left:
        return []
    elif isinstance(truncate, int):
        left = [item[:truncate] for item in left]

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
        formatted = printTable(formatted,
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


def simpleTable(iterable, enum=False, delimiter='=', offset=1, prepend='', print=print):
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
