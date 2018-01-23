# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

__all__ = ['Numeric', 'Number', 'Integer', 'Natural0', 'Natural1', 'Range', 'RangeClosedOpen', 'RangeOpenClosed', 'RangeOpen', 'Positive0', 'Positive', 'NDArray']
import math
from .base import Type, TypeFactory

try:
    import numpy as np
    NUMERIC_TYPES = (int, float, np.integer, np.floating)
    USE_NUMPY = True
except ImportError:
    print("Warning: numpy not found.  Numpy support disabled.")
    NUMERIC_TYPES = (int, float)
    USE_NUMPY = False

class Numeric(Type):
    """Any integer or float, including inf, -inf, and nan."""
    def test(self, v):
        super().test(v)
        assert isinstance(v, NUMERIC_TYPES), "Invalid numeric"
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
        if USE_NUMPY:
            yield np.inf
            yield -np.inf
            yield np.nan
            yield np.int0(0)
            yield np.uint16(1)
            yield np.int0(-1)
            yield np.float16(3.141)
            yield np.float128(.01)
            

class Number(Numeric):
    """Any integer or float, excluding inf, -inf, and nan."""
    def test(self, v):
        super().test(v)
        assert isinstance(v, NUMERIC_TYPES), "Invalid number"
        assert not math.isnan(v), "Number cannot be nan"
        assert not math.isinf(v), "Number must be finite"
    def generate(self):
        yield 0
        yield 1
        yield -1
        yield 3.141 # A float
        yield 1e-10 # A small number
        yield 1e10 # A large number
        if USE_NUMPY:
            yield np.int0(0)
            yield np.uint16(1)
            yield np.int0(-1)
            yield np.float16(3.141)
            yield np.float128(.01)
            yield np.float128(10)

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
        if USE_NUMPY:
            yield np.int16(-10)
            yield np.int8(-1)
            yield np.int64(0)
            yield np.uint0(1)
        
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
        if USE_NUMPY:
            yield np.int16(10)
            yield np.int8(4)
            yield np.int64(0)
            yield np.uint0(1)

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
        if USE_NUMPY:
            yield np.int16(10)
            yield np.int8(4)
            yield np.int64(5)
            yield np.uint0(1)

class Range(Number):
    """Any integer or float from `low` to `high`, inclusive."""
    def __init__(self, low, high):
        super().__init__()
        assert low in Numeric() and high in Numeric(), "Invalid bounds"
        assert not (math.isnan(low) or math.isnan(high)), "Bounds can't be nan"
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
    """A positive number, including zero."""
    def __init__(self):
        return super().__init__(low=0, high=math.inf)
    def generate(self):
        yield 4.3445 # A float
        yield 1
        yield 10
        yield from super().generate()

class Positive(RangeOpen):
    """A positive number, excluding zero."""
    def __init__(self):
        return super().__init__(low=0, high=math.inf)
    def generate(self):
        yield 4.3445 # A float
        yield 1
        yield 10
        yield from super().generate()

class NDArray(Type):
    """A numpy ndarray of dimension `d` and type `typ`."""
    def __init__(self, d=None, typ=None):
        super().__init__()
        assert USE_NUMPY, "Numpy support not enabled"
        if d is not None:
            assert (d in Integer())  and d>0
        # TODO support non-numeric types
        if typ is not None:
            assert issubclass(typ, Numeric)
            self.type = TypeFactory(typ)
        else:
            self.type = None
        self.d = d
    def test(self, v):
        super().test(v)
        if self.d is not None:
            assert len(v.shape) == self.d
        if self.type is not None:
            for fv in v.flatten():
                self.type.test(fv), \
                    "Array value %s is not of type %s" % (fv, repr(self.type))
    def generate(self):
        # TODO fix, and more of these
        # if self.type:
        #     vals = [e for e in self.type.generate()]
        # else:
        #     vals = [0, 1, 2, 3, 4, 5]
        # if self.d and vals:
        #     yield np.broadcast_to(vals[0], self.d)
        # if vals:
        yield np.asarray([-1, 0, 1])

