from mlky import Null


def test_comparisons():
    """
    Null should be roughly equivalent to a None
    """
    assert Null == None, 'Null != None'
    assert Null == Null(), 'Null != Null()'
    assert Null is Null(), 'Null is not Null()'
    assert Null() == Null(), 'Null() != Null()'
    assert bool(Null) == False, 'bool(Null) != False'


def test_attrs():
    """
    Verifies the getattr and setattr pieces work as intended
    """
    assert Null.test is Null, 'Null getattr fails'
    assert Null.test.recursive is Null, 'Null getattr fails recursively'

    Null.test = 1
    Null.test.recursive = 1
    assert Null.test is Null, 'Null setattr fails'
    assert Null.test.recursive is Null, 'Null setattr fails recursively'


def test_warnings(caplog):
    """
    Verifies warnings can be disabled
    """
    # Make sure the previously captured log messages are cleared out
    caplog.clear()

    assert Null._warn, 'Null warning disabled by default'

    Null.test = 1
    message = list(caplog.records)[-1].message
    assert message == 'Null objects cannot take attribute assignments but will not raise an exception'

    caplog.clear()
    Null._warn = False
    Null.test  = 1
    assert caplog.records == [], 'Warnings failed to be disabled'
