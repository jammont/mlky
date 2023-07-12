import os

from mlky import Config, Section
from mlky.configs.definitions import format_defs


os.environ['EMULATOR']     = '/Users/jamesmo/projects/isofit/.idea/sRTMnet'
os.environ['ENGINE']       = '/Users/jamesmo/projects/isofit/.idea/6S'
os.environ['ISOFIT_DEBUG'] = '1'
os.environ['CHUNK']        = 'small'

file = '/Users/jamesmo/projects/mlkyutils/mlky/configs/tests/isofit/config.yml'
defs = '/Users/jamesmo/projects/mlkyutils/mlky/configs/tests/isofit/definitions.yml'

config = Config(file, 'full', defs=defs, _validate=False)

lines, flags = format_defs(config._defs)


#%%
import pandas as pd
import panel as pn

header = pn.Row(
    pn.pane.Str('MLky Configuration Builder', styles={'font-size': '18pt'}),
    min_height = 60,
    width_policy='max',
    styles={'background': 'Grey'}
)

#%%
# left  = pn.Spacer(styles=dict(background='grey'))
rows = []
for line in lines:
    # Split the key and value
    key, *val = line[0].split(': ')
    val = ': '.join(val) # Rejoin in case this substring was in the value

    # Value Pane
    styles = {}
    vpane = pn.pane.Str(val, width_policy='max', styles=styles)

    # Key Pane
    styles = {}
    if not val:
        styles['background'] = 'LightBlue'
    kpane = pn.pane.Str(key, width_policy='max', styles=styles)

    # Row: key pane left, value pane right, each 50% width
    row = pn.Row(kpane, vpane, width_policy='max')
    rows.append(row)

left = pn.Column(*rows, styles={'background': 'Gainsboro'}, scroll=True)
#%%

data = []
for line in lines:
    # Split the key and value
    key, *val = line[0].split(': ')
    val = ': '.join(val) # Rejoin in case this substring was in the value

    # Is section
    if not val:
        key = key[:-1]

    data.append([key, val])

df    = pd.DataFrame(data, columns=['Key', 'Value'])
table = pn.widgets.Tabulator(df, layout='fit_columns')
left  = pn.Column(table, styles={'background': 'Gainsboro'}, scroll=True)
#%%

lvls = int(max(flags, key=lambda flag: flag['level'])['level'])
data = []
for i, line in enumerate(lines):
    lvl = [''] * lvls

    # Split the key and value
    key, *val = line[0].split(': ')

    # Rejoin in case this substring was in the value
    val = ': '.join(val)

    # Is section
    if not val:
        key = key[:-1]

    # Assign
    lvl[int(flags[i]['level']) - 1] = key

    data.append(lvl + [val])

df = pd.DataFrame(data, columns=[f'Level {i}' for i in range(lvls)] + ['Value'])
df = df.set_index(list(df.columns[:-1]))
table = pn.widgets.Tabulator(df, hierarchical=True, layout='fit_columns')
left  = pn.Column(table, styles={'background': 'Gainsboro'}, scroll=True)

#%%

right = pn.Spacer(styles=dict(background='black'))

body = pn.GridSpec(sizing_mode='stretch_both')

body[:, :2] = left
body[:,  2] = right

pn.Column(header, body).servable()

#%%
flags[0]
lines[0]

# help(pn.Row)

12*30
