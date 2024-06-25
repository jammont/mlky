# Definitions

Definition files (shorthand: `defs`) are structured YAML documents designed to guide a `Sect` (which `Config` is a subclass of) object in populating itself and enforcing validation rules.

1. **Population Process**:
   When processing a configuration input, a `Sect` object generates child keys (of type `Sect` or `Var`) based on the definitions provided in the `defs.yml`. If a key is missing in the input but defined in the `defs.yml`, it will be added with default values.

2. **Rule Enforcement**:
   Rules specified in `defs.yml` are applied to the respective key objects within the `Sect`. For example, if a key like `A` is defined with a data type of `int`, attempting to assign any other data type to `A` will result in a validation failure triggered by `Sect.validate()`. Various types of rules, such as `isfile`, `isbetween(val1, val2)`, are supported, alongside the ability to incorporate custom rule functions, known as `checks`.

## How to Construct

### Root Level

`defs.yml` files are structured to start from the *root* level of the `Sect` object. In patch-less instantiations, the root level is the top level of the input. In patched instantiations, the root level is the next level down. For example:

```YAML
A:
  m: ...
B:
  n: ...
```

The above input config patch-less `Sect(config)` will produce:

```YAML
A:
  m: ...
B:
  n: ...
```

The root level in this case is `A, B`, so the `defs` should start with defining these keys.

Whereas using a patch `Sect(data=config, patch="A<-B")`:

```YAML
m: ...
n: ...
```

The root is `m, n`, and as such `defs` will start with these instead.

### Keys

A key of the config starts with a period `.` followed by the name of the key. Definition options do not start with a period `.`.

Assume this is a `defs.yml`:

```YAML
.train:
  default: abc
.test:
  default: xyz
```

And a potential `config.yml`:

```YAML
default:
  train: ijk

mno:
  test: mno

uvw:
  test: uvw

override:
  train: \
```

Possible instantiations:

- Use only the `default` section, pulling the `train` from the `defs`
  ```python
  >>> Sect(data='config.yml', defs='defs.yml', patch=['default'])
  ```
  ```YAML
  train: ijk
  test: xyz
  ```

- Patch section `mno` onto `default`, aka `default<-mno`
  ```python
  >>> Sect(data='config.yml', defs='defs.yml', patch=['default', 'mno'])
  ```
  ```YAML
  train: ijk
  test: mno
  ```

- Use the default value of `train` as set by the `defs` instead of the `default` section
  ```python
  >>> Sect(data='config.yml', defs='defs.yml', patch=['default', 'override'])
  ```
  ```YAML
  train: abc
  test: xyz
  ```

- Now patch the `test` key with the `uvw` section but use the default value of `train` from `defs`
  ```python
  >>> Sect(data='config.yml', defs='defs.yml', patch=['override', 'uvw'])
  ```
  ```YAML
  train: abc
  test: uvw
  ```

### Var keys

`Var` are container objects for keys that are any type other than `dict` or `list` (unless `Sect._opts.convertListTypes` is set to `False`).

The options for a Var key are as follows:

Option | Description | Example
-|-|-
dtype | The expected data type. This can either be a single type or a list of types | `dtype: int`<br>`dtype: [str, int]`
sdesc | Short description for the key | `sdesc: This describes what the key is for`
ldesc | Long description for the key | `ldesc: This is to be an extra long description`
default | Default value to set when not provided. Omit to default to `Null` | `default: 1`<br>`default: abc`
required | Boolean setting this key to be required to be set by the user manually | `required: true`<br>`required: false`
checks | Registered checks to apply to the key | See the [checks](#var-checks) section for more information and examples
items | When the Var is a list type with dict items, this sets the definition for each child | See the [items](#var-items) section for more information and examples
subtypes | | See the [items](#var-subtypes) section for more information and examples

### Var Items

### Var Subtypes

`subtypes` is a special option for Vars that define different types for a given key.

### Sect keys

`Sect` objects can either be explicitly or implicitly defined. To do so explicitly, set `dtype: dict`. Implicitly, if any child key is detected (by checking if any subkey starts with a period), then the dtype is set automatically.

```
.model:
  .kind:
    dtype: str
    default: RandomForestRegressor
  .params:
    dtype: dict
```

The above will be detected to be a `Sect` on creation.

### Rules / Checks

Rules applied via the `defs` are known as `checks`. They are executed when the `.validate()` function is called on either a `Sect` or `Var` object.

### Var Checks

...

### Sect Checks
