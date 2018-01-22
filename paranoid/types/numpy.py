# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

from .base import Type, TypeFactory
import numpy as np

class NPNumeric(Type):
    """Any numpy integer or float, including inf, -inf, and nan."""
    def test(self, v):
        super().test(v)
        assert isinstance(v, np.number), "Invalid numeric"
    def generate(self):
        # Check infinity, nan, 0, +/- numbers, a float, a small/big number
        yield np.inf
        yield -np.inf
        yield np.nan
        yield np.int0(0)
        yield np.uint16(1)
        yield np.int0(-1)
        yield np.float16(3.141)
        yield np.float128(1e-10)
        yield np.float128(1e10)

class NPNumber(NPNumeric):
    """Any numpy real integer or float, excluding inf, -inf, nan, and complex."""
    def test(self, v):
        super().test(v)
        assert isinstance(v, (np.integer, np.floating)), "Invalid number"
        assert not np.isnan(v), "Number cannot be nan"
        assert not np.isinf(v), "Number must be finite"
    def generate(self):
        yield np.int0(0)
        yield np.uint16(1)
        yield np.int0(-1)
        yield np.float16(3.141)
        yield np.float128(1e-10)
        yield np.float128(1e10)

class NPInteger(NPNumber):
    """Any numpy integer."""
    def test(self, v):
        super().test(v)
        assert isinstance(v, np.integer), "Invalid integer"
    def generate(self):
        yield np.int16(-100)
        yield np.int8(-1)
        yield np.int64(0)
        yield np.uint0(1)
        yield np.int16(100)

class NPNatural0(NPInteger):
    """Any numpy natural number including 0."""
    def test(self, v):
        super().test(v)
        assert v >= 0, "Must be greater than or equal to 0"
    def generate(self):
        yield np.int16(0)
        yield np.int8(1)
        yield np.uint16(10)
        yield np.int0(100)

class NPNatural1(NPNatural0):
    """Any numpy natural number excluding 0."""
    def test(self, v):
        super().test(v)
        assert v > 0, "Must be greater than 0"
    def generate(self):
        yield np.int8(1)
        yield np.uint16(10)
        yield np.int0(100)

class NPRange(NPNumber):
    """Any numpy integer or float from `low` to `high`, inclusive."""
    def __init__(self, low, high):
        super().__init__()
        assert isinstance(low, (float, int)) and \
            isinstance(high, (float, int)), "Invalid bounds"
        assert low < high, \
            "Low %s must be strictly greater than high %s" % (low, high)
        # Array conversion is a hack for type coersion, I can't figure
        # out a better way to get python types into numpy types while
        # preserving the int or float status.
        self.low = np.array([low if low is not None else -np.inf])[0]
        self.high = np.array([high if low is not None else np.inf])[0]
    def test(self, v):
        super().test(v)
        assert self.low <= v <= self.high, "Value %f must be greater" \
            "than %f and less than %f" % (v, self.low, self.high)
    def generate(self):
        EPSILON = 1e-5
        if not np.isinf(self.low):
            yield self.low
            yield self.low + EPSILON
        if not np.isinf(self.high):
            yield self.high
            yield self.high - EPSILON
        if not (np.isinf(self.low) or np.isinf(self.high)):
            l = self.low
            h = self.high
            yield l + (h-l)*.25
            yield l + (h-l)*.5
            yield l + (h-l)*.75

class NPArray(Type):
    """A numpy ndarray of dimension `d` and type `typ`.
    """
    def __init__(self, d=None, typ=None):
        super().__init__()
        if d is not None:
            assert isinstance(d, int) and d>0
        # TODO support non-numeric types
        if typ is not None:
            assert issubclass(type(typ), NPNumeric)
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
        yield np.asarray([-1, 0, 1])

