# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

__all__ = ['Numeric', 'Number', 'Integer', 'Natural0', 'Natural1', 'Range', 'RangeClosedOpen', 'RangeOpenClosed', 'RangeOpen', 'Positive0', 'Positive']
import math
from .base import Type

class Numeric(Type):
    """Any integer or float, including inf, -inf, and nan."""
    def test(self, v):
        super().test(v)
        assert isinstance(v, (int, float)), "Invalid numeric"
    def generate(self):
        # Check infinity, nan, 0, +/- numbers, a float, a small/big number
        yield math.inf # Check infs
        yield -math.inf
        yield math.nan # nan
        yield 0
        yield 1
        yield -1
        yield 3.141 # A float
        yield 1e-10 # A small number
        yield 1e10 # A big number

class Number(Numeric):
    """Any integer or float, excluding inf, -inf, and nan."""
    def test(self, v):
        super().test(v)
        assert isinstance(v, (int, float)), "Invalid number"
        assert not math.isnan(v), "Number cannot be nan"
        assert not math.isinf(v), "Number must be finite"
    def generate(self):
        yield 0
        yield 1
        yield -1
        yield 3.141 # A float
        yield 1e-10 # A small number
        yield 1e10 # A large number

class Integer(Number):
    """Any integer."""
    def test(self, v):
        super().test(v)
        assert v // 1 == v, "Invalid integer"
    def generate(self):
        yield -100
        yield -1
        yield 0
        yield 1
        yield 100

class Natural0(Integer):
    """Any natural number including 0."""
    def test(self, v):
        super().test(v)
        assert v >= 0, "Must be greater than or equal to 0"
    def generate(self):
        yield 0
        yield 1
        yield 10
        yield 100

class Natural1(Natural0):
    """Any natural number excluding 0."""
    def test(self, v):
        super().test(v)
        assert v > 0, "Must be greater than 0"
    def generate(self):
        yield 1
        yield 2
        yield 10
        yield 100

class Range(Number):
    """Any integer or float from `low` to `high`, inclusive."""
    def __init__(self, low, high):
        super().__init__()
        assert isinstance(low, (float, int)) and \
            isinstance(high, (float, int)), "Invalid bounds"
        assert low < high, \
            "Low %s must be strictly greater than high %s" % (low, high)
        assert not (math.isinf(low) and math.isinf(high)), \
            "Both bounds can't be inf"
        self.low = low if low is not None else -math.inf
        self.high = high if low is not None else math.inf
    def test(self, v):
        super().test(v)
        assert self.low <= v <= self.high, "Value %f must be greater" \
            "than %f and less than %f" % (v, self.low, self.high)
    def generate(self):
        EPSILON = 1e-5
        if not math.isinf(self.low):
            yield self.low
            yield self.low + EPSILON
        if not math.isinf(self.high):
            yield self.high
            yield self.high - EPSILON
        if not (math.isinf(self.low) or math.isinf(self.high)):
            l = self.low
            h = self.high
            yield l + (h-l)*.25
            yield l + (h-l)*.5
            yield l + (h-l)*.75

class RangeClosedOpen(Range):
    """A half open interval from `low` (closed) to `high` (open)."""
    def test(self, v):
        super().test(v)
        assert v != self.high, "Value must be strictly greater than %f" % self.high
    def generate(self):
        for v in super().generate():
            if v != self.high:
                yield v

class RangeOpenClosed(Range):
    """A half open interval from `low` (open) to `high` (closed)."""
    def test(self, v):
        super().test(v)
        assert v != self.low, "Value must be strictly less than %f" % self.low
    def generate(self):
        for v in super().generate():
            if v != self.low:
                yield v

class RangeOpen(RangeClosedOpen, RangeOpenClosed):
    """Any number in the open interval from `low` to `high`."""
    def test(self, v):
        super().test(v)
    def generate(self):
        for v in Range.generate(self):
            if not v in [self.low, self.high]:
                yield v

class Positive0(RangeClosedOpen):
    def __init__(self):
        return super().__init__(low=0, high=math.inf)
    def generate(self):
        yield 4.3445 # A float
        yield 1
        yield 10
        yield from super().generate()

class Positive(RangeOpen):
    def __init__(self):
        return super().__init__(low=0, high=math.inf)
    def generate(self):
        yield 4.3445 # A float
        yield 1
        yield 10
        yield from super().generate()
