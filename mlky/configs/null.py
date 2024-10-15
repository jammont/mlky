"""
The Null class of mlky.
"""
import dis
import inspect
import logging

from datetime import datetime as dtt


Logger = logging.getLogger(__file__)


def NullErrors(msg, warn):
    """
    Attempt to track how many errors are occurring on Null objects. If the errors
    amount to more than 1k within seconds, raise an exception to prevent an endless
    loop.
    """
    now = dtt.now()

    elapse = (now - NullErrors.now).total_seconds()
    if elapse < 1:
        NullErrors.err += 1
    else:
        NullErrors.err = 0

    if warn and elapse > .1:
        Logger.warning(msg)

    NullErrors.now = now

    if NullErrors.err >= 1000:
        raise RuntimeError("Endless loop of errors detected (more than 1k errors per second), killing fault tolerance")

NullErrors.now = dtt.now()
NullErrors.err = 0


def debug(msg):
    """
    Utility function to quickly enable debug logging for this module

    Parameters
    ----------
    msg : any
        Message to print
    """
    if Null._debug:
        if msg == 'exception':
            Logger.exception('An exception was caught:')
        else:
            Logger.error(msg)


def traceNull(frame):
    """
    Traces the source of the Null object in a given frame. Designed to only detect
    calls on Nulls and not all Null objects.

    Returns
    -------
    str or None
        If the source Null can be identified, returns the string, otherwise None
    """
    paths = []
    path  = ''
    obj   = None

    line = '─'*64
    debug(f'┌{line}')
    for instr in dis.Bytecode(frame.f_code):
        debug('¦ ' + str(instr))
    debug(f'└{line}')

    debug(f'┌{line}')

    for instr in dis.Bytecode(frame.f_code):
        debug('¦    ' + str(instr))

        if instr.opname == 'LOAD_NAME':
            path = instr.argval
            obj  = frame.f_locals.get(path)
            debug(f'┌─ Loading local: {path}')

        elif instr.opname == 'LOAD_GLOBAL':
            path = instr.argval
            obj  = frame.f_globals.get(path)
            debug(f'┌─ Loading global: {path}')

        elif instr.opname in ('LOAD_ATTR', 'LOAD_METHOD') and obj is not None:
            if obj is not Null:
                path += f'.{instr.argval}'
            try:
                obj = obj[instr.argval]
            except:
                obj = None
            debug(f'├─ Loaded attr/method: {instr.argval}')

        elif instr.opname == 'CALL_METHOD' and obj is Null:
            # Null identified, reset working object
            obj = None
            paths.append(path)
            debug(f'└─ Call method, obj is null, appending path: {path}')

        # else:
        #     obj = None
        #     debug('└─ Resetting obj to None')

    debug(f'└{line}')

    # Return the unique set to paths
    return set(paths)

def getContext():
    """
    Retrieves the last frame context for debugging

    Returns
    -------
    str
        Formatted context string
    """
    # Caller frame is two frames back
    frame = inspect.currentframe().f_back.f_back
    info  = inspect.getframeinfo(frame)
    trace = traceNull(frame)

    context = f'\n    {info.code_context[0].strip()}' if info.code_context else ''
    context = f'Context:\n  File "{info.filename}", line {info.lineno}, in {info.function}{context}'
    if trace:
        if len(trace) > 1:
            pad   = '\n    - '
            paths = pad.join(trace)
            paths = pad + paths
        else:
            paths = trace.pop()

        context += f'\n    Identified as Null: {paths}'

    return context


class NullType(type):
    """
    Acts like a Nonetype (generally) without raising an exception in common use
    cases such as:
    - __getattr__, __getitem__ will return itself, preventing raising missing
    attribute. Ex: config.this_key_is_missing.also_missing will return Null.
    - Dict functions .get, .keys, and .items will return empty lists/dicts.
    - Comparisons should always return False unless compared to a None or Null
    type.

    Warnings can be disabled via:
    >>> Null._warn = False
    """
    _warn  = True
    _debug = False

    def __call__(cls, *args, **kwargs):
        try:
            context = getContext()
        except:
            debug('exception')
            context = ''

        NullErrors(f'Null received a call like a function, was this intended? {context}', cls._warn)

        return cls

    def __deepcopy__(self, memo):
        return type(self)()

    def __hash__(cls):
        return hash(None)

    def __bool__(cls):
        return False

    def __or__(cls, other):
        return other

    def __contains__(cls):
        return False

    def __eq__(cls, other):
        return type(other) in [type(None), type(cls)]

    def __iter__(cls):
        return iter({})

    def __setattr__(cls, key, value):
        if key in ('_warn', '_debug'):
            super().__setattr__(key, value)
            return

        NullErrors('Null objects cannot take attribute assignments but will not raise an exception', cls._warn)

    def __getattr__(cls, key):
        return cls

    def __setitem__(cls, key, value):
        setattr(cls, key, value)

    def __getitem__(cls, key):
        return cls

    def __str__(cls):
        return 'Null'

    def __repr__(cls):
        return 'Null'

    def get(self, key, other=None, **kwargs):
        return other

    def keys(self):
        return []

    def items(self):
        return ()


class Null(metaclass=NullType):
    ...


class NullDict(dict):
    """
    Simple dict extension that enables dot notation and defaults to Null when an
    item/attribute is missing
    """
    def __deepcopy__(self, memo):
        new = type(self)(self)
        memo[id(self)] = new
        return new

    def __getattr__(self, key):
        return super().get(key, Null)

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __setattr__(self, key, value):
        self[key] = value
