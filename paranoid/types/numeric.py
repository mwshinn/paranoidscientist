# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

__all__ = ['Numeric', 'ExtendedReal', 'Number', 'Integer', 'Natural0', 'Natural1', 'Range', 'RangeClosedOpen', 'RangeOpenClosed', 'RangeOpen', 'Positive0', 'Positive', 'NDArray']
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
            yield np.float64(.01)

class ExtendedReal(Numeric):
    """Any integer or float, excluding nan."""
    def test(self, v):
        super().test(v)
        assert not math.isnan(v), "Number cannot be nan"
    def generate(self):
        # Check infinity, nan, 0, +/- numbers, a float, a small/big number
        yield math.inf # Check infs
        yield -math.inf
        yield 0
        yield 1
        yield -1
        yield 3.141 # A float
        yield 1e-10 # A small number
        yield 1e10 # A big number
        if USE_NUMPY:
            yield np.inf
            yield -np.inf
            yield np.int0(0)
            yield np.uint16(1)
            yield np.int0(-1)
            yield np.float16(3.141)
            yield np.float64(.01)

class Number(Numeric):
    """Any integer or float, excluding inf, -inf, and nan."""
    def test(self, v):
        super().test(v)
        assert isinstance(v, NUMERIC_TYPES), "Invalid number"
        assert not math.isinf(v), "Number must be finite"
        assert not math.isnan(v), "Number cannot be nan"
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
            yield np.float64(.01)
            yield np.float64(10)

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

class Natural1(Integer):
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
    """Any integer or float from `low` to `high`, inclusive.

    Note that this does NOT include correction for floating point
    roundoff errors.  This is because, if there are floating point
    roundoff errors, some code may fail.
    """
    def __init__(self, low, high):
        super().__init__(low, high)
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

class RangeOpen(Range):
    """Any number in the open interval from `low` to `high`."""
    def test(self, v):
        super().test(v)
        assert v != self.low
        assert v != self.high
    def generate(self):
        for v in Range.generate(self):
            if not v in [self.low, self.high]:
                yield v

class Positive0(Number):
    """A positive number, including zero."""
    def test(self, v):
        super().test(v)
        assert v >= 0
    def generate(self):
        yield 4.3445 # A float
        yield 1
        yield 10
        yield 0

class Positive(Number):
    """A positive number, excluding zero."""
    def test(self, v):
        super().test(v)
        assert v > 0
    def generate(self):
        yield 4.3445 # A float
        yield 1
        yield 10

class NDArray(Type):
    """A numpy ndarray of dimension `d` and type `t`."""
    def __init__(self, d=None, t=None):
        super().__init__(d=d, t=t)
        assert USE_NUMPY, "Numpy support not enabled"
        if d is not None:
            assert (d in Integer())  and d>0
        # TODO support non-numeric types
        if t is not None:
            assert isinstance(TypeFactory(t), Type)
            self.type = TypeFactory(t)
        else:
            self.type = None
        self.d = d
    def test(self, v):
        super().test(v)
        assert isinstance(v, np.ndarray), "V is not an NDArray, it is a " + str(type(v))
        if self.d is not None:
            assert len(v.shape) == self.d
        if self.type is not None:
            # Optimizing this for numbers, which are used often
            if type(self.type) is Number:
                assert np.all(np.isfinite(v))
            elif type(self.type) is Positive:
                assert np.all(np.isfinite(v))
                assert np.all(v > 0)
            elif type(self.type) is Positive0:
                assert np.all(np.isfinite(v))
                assert np.all(v >= 0)
            else:
                for fv in v.flatten():
                    assert fv in self.type, "Array value %s is not of type %s" % (fv, repr(self.type))
    def generate(self):
        # TODO fix, and more of these
        if self.type:
            vals = [e for e in self.type.generate()]
        else:
            vals = [3, 4, 5, 6, 7, 8, 9, 10]
        if self.d:
            dimspecs = [tuple([5]*self.d)]
        else:
            dimspecs = [(20,), (5,5), (3,3,3), (200,)]
        # Check basic values
        if not self.type or 0 in self.type:
            yield np.zeros(dimspecs[0], dtype=np.float64)
        if not self.type or 1 in self.type:
            yield np.ones(dimspecs[0], dtype=np.int32)
        if not self.type or -1 in self.type:
            yield -np.ones(dimspecs[0])
        if not self.type or np.nan in self.type:
            yield np.ones(dimspecs[0])*np.nan
        if not self.type or np.inf in self.type:
            yield np.ones(dimspecs[0])*np.inf
        if not self.type or -np.inf in self.type:
            yield np.ones(dimspecs[0])*-np.inf
        # Check all dimensions
        for d in dimspecs:
            yield np.tile(vals[0], d)
        # Check for arrays with not a single value
        lenneeded = int(np.prod(dimspecs[0]))
        copies = int(np.ceil(lenneeded/len(vals)))
        yield np.reshape((vals*copies)[0:lenneeded], dimspecs[0])

