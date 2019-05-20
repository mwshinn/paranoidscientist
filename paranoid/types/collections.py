# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

__all__ = ['Set', 'List', 'Tuple', 'Dict', 'ParametersDict', ]
from .base import Type, TypeFactory

class Set(Type):
    """Any element which is a member of `els`.

    `els` can be one of several standard Python types, including a
    list, a tuple, or a set.  Any object with the __contains__
    function is valid.  This ensures that a value is contained within
    `els`.
    """
    def __init__(self, els):
        super().__init__(els)
        assert hasattr(els, "__contains__") and callable(els.__contains__)
        self.els = els
    def test(self, v):
        super().test(v)
        assert v in self.els, "Value %s in set" % v
    def generate(self):
        for e in self.els:
            yield e

class List(Type):
    """A Python list."""
    def __init__(self, t):
        super().__init__(t)
        self.type = TypeFactory(t)
    def test(self, v):
        super().test(v)
        assert isinstance(v, list), "Non-list passed"
        for e in v:
            self.type.test(e)
    def generate(self):
        yield [] # Empty list
        yield [gv for gv in self.type.generate()] # A list of those types
        yield [next(self.type.generate())]*1000 # A long list

class Tuple(Type):
    """A Python tuple."""
    def __init__(self, *args):
        self.types = [TypeFactory(t) for t in args]
        super().__init__(*self.types)
    def test(self, v):
        super().test(v)
        assert isinstance(v, tuple), "Non-tuple passed"
        assert len(v) == len(self.types)
        for i in range(0, len(v)):
            self.types[i].test(v[i])
    def generate(self):
        yield tuple([next(t.generate()) for t in self.types]) # A tuple of the passed types

class Dict(Type):
    """A Python dictionary."""
    def __init__(self, k, v):
        self.valtype = TypeFactory(v)
        self.keytype = TypeFactory(k)
        super().__init__(k=self.keytype, v=self.valtype)
    def test(self, v):
        super().test(v)
        assert isinstance(v, dict), "Non-dict passed"
        for e in v.keys():
            self.keytype.test(e)
        for e in v.values():
            self.valtype.test(e)
    def generate(self):
        yield {}
        yield dict(zip(self.keytype.generate(), self.valtype.generate()))

class ParametersDict(Type):
    """A Python dictionary with limited keys.

    Represents a set of parameters.  `params`, the single argument,
    should be a dictionary, where the keys are strings representing
    the parameter names the values are Types.  The only keys allowed
    in a ParametersDict are the keys in `params`.  The values for each
    key must be of the type specified.  Note that not all of the keys
    in `params` must be specified for this type to be valid.
    """
    def __init__(self, params, all_mandatory=False):
        # Future note: if this is modified to work with non-strings
        # for keys, then adjust the test() function accordingly, in
        # particular, the line checking that there are no extra keys
        # for objects with equality implemented by memory location
        # instead of value.
        assert all((isinstance(k, str) for k in params.keys()))
        self.params = {k: TypeFactory(v) for k,v in params.items()}
        assert all_mandatory in [True, False]
        self.all_mandatory = all_mandatory
        super().__init__(self.params, all_mandatory=all_mandatory)
    def test(self, v):
        super().test(v)
        assert isinstance(v, dict), "Non-dict passed"
        assert not set(v.keys()) - set(self.params.keys()), \
            "Invalid reward keys"
        if self.all_mandatory:
            assert set(v.keys()) == set(self.params.keys()), \
                "All keys are mandatory, but missing: " + \
                str(set(self.params.keys()) - set(v.keys()))
        for k in v.keys():
            self.params[k].test(v[k])
    def generate(self):
        yield {k : next(self.params[k].generate()) for k in self.params.keys()}
        if self.all_mandatory == False:
            yield {}
            # TODO more appropriate tests here
            for k in self.params.keys():
                yield {k : next(self.params[k].generate())}

