import os

from mlky import (
    Config,
    register
)

os.environ['EMULATOR']     = '/Users/jamesmo/projects/isofit/.idea/sRTMnet'
os.environ['ENGINE']       = '/Users/jamesmo/projects/isofit/.idea/6S'
os.environ['ISOFIT_DEBUG'] = '1'
os.environ['CHUNK']        = 'small'

#%% registers.py

config = Config()

@register()
def implementation_mode(value):
    """
    """
    if value != 'simulation' and not config.implementation.inversion:
            return 'If running outside of simulation mode, config.implementation.inversion must be defined'
    return True

@register()
def implementation_ray(value):
    ip = config.implementation.ip_head
    pw = config.implementation.redis_password

    if not (ip and pw) and (ip or pw):
        return 'If either ip_head or redis_password are specified, both must be specified'

    return True

#%%

conf = Config('mlky/configs/tests/isofit/config.yml', 'full', defs='mlky/configs/tests/isofit/definitions.yml', _raise=False)



#%%

_ = conf.template_(file='mlky/configs/tests/isofit/template.nocomments.yml', comments=None)

#%%

_ = conf.template_(file='mlky/configs/tests/isofit/template.inline.yml', comments='inline')

#%%

_ = conf.template_(file='mlky/configs/tests/isofit/template.coupled.yml', comments='coupled')

#%%

c = Config('mlky/configs/tests/isofit/template.nocomments.yml', 'default', local=True)
c

#%%
