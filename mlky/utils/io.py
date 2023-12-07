"""
IO related utilities
"""
import os
import pickle
import yaml


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
