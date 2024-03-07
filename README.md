# mlky

Because it's the only Way.

## What is mlky?

mlky is a versatile Python configuration software package designed by data scientists at the Jet Propulsion Laboratory to cater to the needs of research projects and machine learning pipelines. Originally conceived as a collection of utility scripts and functions, mlky has evolved into a comprehensive configuration package that prioritizes flexibility, robustness, and scalability.

## Installation

You can install mlky using pip:

```bash
pip install mlky
```

Or via Conda:

```bash
conda install -c jammont mlky
```

## Features

- **Configuration Inheritance**: The core of mlky is the inheritance structure that enables configuration sections to inherit from others. This empowers users to craft intricate configuration setups, overriding keys, subkeys, and updating values as needed.

- **Forgiving or Restrictive**: mlky imposes minimal requirements right out of the box. With the custom-built `Null` class, mlky avoids raising exceptions when pieces of the configuration are absent. This allows developers to focus on developing their code and less on developing their configuration structures. However, mlky also provides the tools for developers to restrict exactly what configurations consist of. The flexibility of your configuration is for you to define!

- **Customizable Restriction**: While flexibility is paramount, mlky uniquely provides developers the ability to enforce restrictions on a per-key basis. Error-checking, type-checking, type-coercion, and custom parse functions are supported, enabling fine-grained control over configuration options.

- **TRL Scalability**: mlky is designed to assist projects scaling the Technology Readiness Levels ([TRL](https://www.nasa.gov/directorates/heo/scan/engineering/technology/technology_readiness_level)). At low-TRLs, mlky offers its maximum flexibility by providing minimal setup, simple syntax, and forgiving fault tolerance. Once time for a project to mature, mlky assists achieving higher TRLs by providing the framework to set rigid configuration requirements, template generation, and custom error checking.

## Usage

To get started with mlky, import the `Config` class and pass it either a yaml file, yaml string, or a dict:

```python
>>> from mlky import Config
# Empty initially
>>> Config
<Config . (Attrs=[], Sects=[])>
# Now initialized
>>> Config({'A': {'a': 1, 'b': 2}, 'B': {'a': 0, 'c': 3}})
<Config . (Attrs=[], Sects=['A', 'B'])>
```

The `Config` object supports both dot and dict notation:

```python
>>> Config.A
<Sect .A (Attrs=['a', 'b'], Sects=[])>
>>> Config['B']
<Sect .B (Attrs=['a', 'c'], Sects=[])>
>>> Config.A.a
1
>>> Config['B']['a']
0
>>> Config['A'].b
2
>>> Config.B['c']
3
```

It is also a singleton, though that can be overridden with the `local=True` parameter:

```python
def set_param(key, value, local=False):
  config = Config(local=local)
  config[key] = value

def get_param(key, local=False):
  config = Config(local=local)
  return config[key]

>>> set_param('persist', True) # Global
>>> get_param('persist') # Global
True
>>> set_param('local', True, local=True)
>>> get_param('local')
Null
>>> get_param('persist', local=True) # Copies global instance
True
```

Because it is a singleton, you can also use `Config` directly instead of a variable as well as use the class across the Python instance:

```python
# Script 1
from mlky import Config

Config(a=1, b=2) # initialize somewhere
```
```python
# Script 2
from mlky import Config

Config.a == 1
Config.b == 2
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

Please see the docs for more information.

## Contributing

We welcome contributions from the community. If you'd like to contribute to mlky, please follow these steps:

1. Fork the repository and clone it locally.
2. Create a new branch for your feature or bug fix.
3. Make your changes and ensure tests pass.
4. Commit your changes and push them to your fork.
5. Open a pull request with a detailed description of your changes.

## License

mlky is distributed under the [Apache v2.0 License](https://opensource.org/license/apache-2-0/). Feel free to use, modify, and distribute it according to the terms of the license.

---

Explore the power of flexible and robust configuration with mlky, the configuration package built by data scientists, for data scientists. Whether you're working on a small project or a complex system, mlky adapts to your needs and helps you streamline your configuration process.
