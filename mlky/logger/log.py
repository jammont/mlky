import contextlib

@contextlib.contextmanager
def themeter(name):
    theobj = Meter(name)
    try:
        yield theobj
    finally:
        theobj.close()  # or whatever you need to do at exit


# usage
with themeter('/dev/ttyS2') as m:
    # do what you need with m
    m.read()
