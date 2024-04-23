"""
Tracks and reports the percentage complete for some arbitrary sized iterable

Usage
-----
>>> from mlky.utils.track import Track
>>> data = [0] * 77
>>> report = Track(data)
>>> for i in range(len(data)+1):
...   report(i)
  5.00% complete (elapsed: 0:00:00.000028, rate: 0:00:00, eta: 0:00:00.000532)
 10.00% complete (elapsed: 0:00:00.000099, rate: 0:00:00.000001, eta: 0:00:00.000891)
 15.00% complete (elapsed: 0:00:00.000106, rate: 0:00:00.000001, eta: 0:00:00.000601)
 20.00% complete (elapsed: 0:00:00.000112, rate: 0:00:00.000001, eta: 0:00:00.000448)
 25.00% complete (elapsed: 0:00:00.000117, rate: 0:00:00.000001, eta: 0:00:00.000351)
 30.00% complete (elapsed: 0:00:00.000122, rate: 0:00:00.000001, eta: 0:00:00.000285)
 35.00% complete (elapsed: 0:00:00.000127, rate: 0:00:00.000001, eta: 0:00:00.000236)
 40.00% complete (elapsed: 0:00:00.000132, rate: 0:00:00.000001, eta: 0:00:00.000198)
 45.00% complete (elapsed: 0:00:00.000136, rate: 0:00:00.000001, eta: 0:00:00.000166)
 50.00% complete (elapsed: 0:00:00.000141, rate: 0:00:00.000001, eta: 0:00:00.000141)
 55.00% complete (elapsed: 0:00:00.000146, rate: 0:00:00.000001, eta: 0:00:00.000119)
 60.00% complete (elapsed: 0:00:00.000151, rate: 0:00:00.000002, eta: 0:00:00.000101)
 65.00% complete (elapsed: 0:00:00.000156, rate: 0:00:00.000002, eta: 0:00:00.000084)
 70.00% complete (elapsed: 0:00:00.000160, rate: 0:00:00.000002, eta: 0:00:00.000069)
 75.00% complete (elapsed: 0:00:00.000165, rate: 0:00:00.000002, eta: 0:00:00.000055)
 80.00% complete (elapsed: 0:00:00.000170, rate: 0:00:00.000002, eta: 0:00:00.000042)
 85.00% complete (elapsed: 0:00:00.000175, rate: 0:00:00.000002, eta: 0:00:00.000031)
 90.00% complete (elapsed: 0:00:00.000179, rate: 0:00:00.000002, eta: 0:00:00.000020)
 95.00% complete (elapsed: 0:00:00.000184, rate: 0:00:00.000002, eta: 0:00:00.000010)
100.00% complete (elapsed: 0:00:00.000189, rate: 0:00:00.000002, eta: 0:00:00)
"""
from datetime import datetime as dtt


class Track:
    """
    Tracks and reports the percentage complete for some arbitrary sized iterable
    """
    def __init__(self, total, step=5, print=print, reverse=False, message="complete"):
        """
        Parameters
        ----------
        total: int, iterable
            Total items in iterable. If iterable, will call len() on it
        step: float, default=5
            Step size to use for reporting
        absolute: int, default=None
            Changes the return
        print: func, default=print
            Print function to use, eg. logging.info
        reverse: bool, default=False
            Reverse the count such that 0 is 100%
        message: str, default="complete"
            Message to be included in the output
        """
        if hasattr(total, '__len__'):
            total = len(total)

        if step > 100:
            raise AttributeError('Step size should be an integer representing a percentage, eg. 5 = report every 5%')

        self.step = step
        self.total = total
        self.print = print
        self.start = dtt.now()
        self.percent = step
        self.reverse = reverse
        self.message = message

    def __call__(self, count):
        """
        Parameters
        ----------
        count: int, iterable
            The current count of items finished. If iterable, will call len() on it

        Returns
        -------
        bool
            True if a percentage step was just crossed, False otherwise
        """
        if hasattr(count, '__iter__'):
            count = len(count)

        current = count / self.total
        if self.reverse:
            current = 1 - current
        current *= 100

        if current >= self.percent:
            elap = dtt.now() - self.start
            rate = elap / self.total
            esti = 100 / self.percent * elap - elap

            self.print(f"{current:6.2f}% {self.message} (elapsed: {elap}, rate: {rate}, eta: {esti})")
            self.percent += self.step

            return True
        return False
