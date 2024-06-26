# Getting Started

mlky is recommended to be installed via pip at this time.

## Installation

You can install mlky using pip:

```bash
pip install mlky
```

Or via Conda:

```bash
conda install -c jammont mlky
```

## Quick Overview

To get started with mlky, import the `Config` object and pass it either a yaml file, yaml string, or a dict:

```python
>>> from mlky import Config
# Empty initially
>>> Config
D{}
# Now initialized
>>> Config({'A': {'a': 1, 'b': 2}, 'B': {'a': 0, 'c': 3}, 'C': ['d', 'e']})
D{'A': D{'a': V=1, 'b': V=2}, 'B': D{'a': V=0, 'c': V=3}, 'C': L[V='d', V='e']}
```

The object uses tags to represent what each part is:

- `D{...}` for `dict` objects
- `L[...]` for `list` objects
- `V=...`  for variable objects

These can be accessed by either dot and dict notation:

```python
>>> Config.A
D{'a': V=1, 'b': V=2}
>>> Config['B']
D{'a': V=0, 'c': V=3}
>>> Config.A.a
1
>>> Config['B']['a']
0
>>> Config['A'].b
2
>>> Config.B['c']
3
```

The `Config` object is also a singleton, though copies can be created to create local versions:

```python
def set_param(key, value, copy=False):
    if copy:
        config = Config.deepCopy()
    else:
        config = Config()

    config[key] = value

def get_param(key, copy=False):
    if copy:
        config = Config.deepCopy()
    else:
        config = Config()
    return config[key]

>>> set_param('persist', True) # Global
>>> get_param('persist') # Global
True
>>> set_param('local', True, copy=True)
>>> get_param('local')
Null
>>> get_param('persist', copy=True) # Copies global instance
True
```

Because it is a singleton, you can also use `Config` directly instead of a variable as well as use the object across the Python instance:

```python
# Script 1
from mlky import Config

Config(a=1, b=2) # initialize somewhere
```
```python
# Script 2
from mlky import Config

assert Config.a == 1
assert Config.b == 2
```

Ideally you would want to initialize the `Config` object at the beginning and then leverage the global instance:

```python
from mlky import Config

def process(item):
  if Config.param:
    ...

def main():
  for item in Config.process:
    process(item)

if __name__ == '__main__':
  Config('/some/config.yaml')
  main()
```

## Detailed Walkthrough

The following will be used as an example:

```python
from glob import glob

from mlky import Config

def process(files):
  for file in files:
    with open(file, 'r') as f:
      lines = f.readlines()

    if Config.skip_header:
      lines = lines[Config.header:]

    ... # Some arbitrary other processing code

    if Config.output:
      with open(Config.output.file, 'a') as f:
        f.writelines(lines)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-c', '--config', required=True)
  parser.add_argument('-p', '--patch')
  args = parser.parse_args()

  Config(args.config, args.patch)

  if Config.get('input'):
    files = glob(f'{Config.input}/*')
    process(files)
  else:
    print('Error: No input provided!')
```

Command: `python script.py -c /some/config.yml -p sect1<-sect2`

Calling the script with the above command will step through:

  1. Initialize the global `Config` instance with the file and patch provided
    a. That is, `sect1` in the `config.yml` will be patched with `sect2`
  2. Check if `Config.input` exists
    a. If it is in the Config, return it as-is. If it is not, this will be a `Null` value which evaluates to `False`
  3. Use the value at `Config.input` to glob some directory
  4. Process the collected files
  5. For each file, read in the data
  6. If `Config.skip_header` is defined, use the (expected to be an int) value of `Config.header`
    a. It is on the user to ensure proper safeguards are inplace.<br>
    b. Multiple possible safeguards include:
      1. `int(Config.header)` to raise an exception if the value cannot be casted to an integer
      2. `Config.get('header', 5)` to use a default value if this key is not in the config
      3. A definitions file to ensure this key is an int (safest)
  7. Check if `Config.output` is defined, which is expected to be a Sect
  8. Append write data to `Config.output.file`
