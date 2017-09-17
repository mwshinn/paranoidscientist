#!/usr/bin/python

import math
import random
import itertools

def TypeFactory(v):
    if issubclass(type(v), Type):
        return v
    elif issubclass(v, Type):
        return v()
    elif issubclass(type(v), type):
        return Generic(v)
    else:
        raise AssertionError

class Type():
    def test(self, v):
        pass

class Generic(Type):
    def __init__(self, typ):
        super().__init__()
        assert isinstance(t, type)
        self.type = typ
    def test(self, v):
        assert isinstance(type(v), self.type)
    def generate(self):
        raise NotImplementedError

class Numeric(Type):
    def test(self, v):
        super().test(v)
        assert isinstance(v, (int, float)), "Invalid number"
    def generate(self):
        # Check infinity, nan, 0, +/- numbers, a float, a small/big number
        return [math.inf, -math.inf, math.nan, 0, 1, -1, 3.141, 1e-10, 1e10]

class Number(Numeric):
    def test(self, v):
        super().test(v)
        assert isinstance(v, (int, float)), "Invalid number"
        assert not math.isnan(v), "Number cannot be nan"
        assert not math.isinf(v), "Number must be finite"
    def generate(self):
        return [0, 1, -1, 3.141, 1e-10, 1e10]

class Integer(Number):
    def test(self, v):
        super().test(v)
        assert v // 1 == v, "Invalid integer"
    def generate(self):
        return [-100, -1, 0, 1, 100]

class Natural0(Integer):
    def test(self, v):
        super().test(v)
        assert v >= 0, "Must be greater than or equal to 0"
    def generate(self):
        return [0, 1, 10, 100]

class Natural1(Natural0):
    def test(self, v):
        super().test(v)
        assert v > 0, "Must be greater than 0"
    def generate(self):
        return [1, 2, 10, 100]

class Range(Number):
    def __init__(self, low, high):
        super().__init__()
        assert isinstance(low, (float, int)) and isinstance(high, (float, int)), "Invalid bounds"
        self.low = low if low is not None else -math.inf
        self.high = high if low is not None else math.inf
    def test(self, v):
        super().test(v)
        assert self.low <= v <= self.high
    def generate(self):
        vals = [self.low, self.high]
        if not (math.isinf(self.low) or math.isinf(self.high)):
            l = self.low
            h = self.high
            vals.append([(l+h)*.5, (l+h)*.25, (l+h)*.75])
        return vals

class RangeClosedOpen(Range):
    def test(self, v):
        super().test(v)
        assert v != self.high

class RangeOpenClosed(Range):
    def test(self, v):
        super().test(v)
        assert v != self.low

class RangeOpen(RangeClosedOpen, RangeOpenClosed):
    def test(self, v):
        super().test(v)

class Set(Type):
    def __init__(self, els):
        super().__init__()
        assert hasattr(els, "__contains__") and callable(els.__contains__)
        self.els = els
    def test(self, v):
        super().test(v)
        assert v in self.els, "Not in set"
    def generate(self):
        return [e for e in self.els]

class String(Type):
    def test(self, v):
        super().test(v)
        assert isinstance(v, str)
    def generate(self):
        return ["", "a"*1000, "{100}", " ", "abc123", "two words", "\\", "%s", "1", "баклажан"]

class List(Type):
    def __init__(self, t):
        super().__init__()
        self.type = TypeFactory(t)
    def test(self, v):
        super().test(v)
        assert isinstance(v, list)
        for e in v:
            self.type.test(e)
    def generate(self):
        return [[], self.type.generate(), [self.type.generate()[0]]*1000]

class Dict(Type):
    def __init__(self, k, v):
        self.valtype = TypeFactory(v)
        self.keytype = TypeFactory(k)
    def test(self, v):
        super().test(v)
        assert isinstance(v, dict)
        for e in v.keys():
            self.keytype.test(e)
        for e in v.values():
            self.valtype.test(e)
    def generate(self):
        return [{}, dict(zip(self.keytype.generate(), self.valtype.generate()))]
            

class And(Type):
    def __init__(self, *types):
        self.types = [TypeFactory(a) for a in types]
    def test(self, v):
        for t in self.types:
            t.test(v)

class Or(Type):
    def __init__(self, *types):
        self.types = [TypeFactory(a) for a in types]
    def test(self, v):
        passed = False
        for t in self.types:
            try:
                t.test(v)
                passed = True
            except AssertionError:
                continue
        if passed == False:
            raise AssertionError

def accepts(*argtypes, **kwargtypes):
    assert len(argtypes)+len(kwargtypes) > 0, "No arguments to accepts"
    def decorator(func):
        assert not hasattr(func, "__accepts__")
        targs = [TypeFactory(a) for a in argtypes]
        tkwargs = {k : TypeFactory(a) for k,a in kwargtypes.items()}
        def decorated(*args, **kwargs):
            assert len(argtypes) == len(args), \
                "Invalid number of decorator arguments"
            assert all(k in kwargs.keys() for k in kwargtypes.keys()), \
                "Invalid decorator keyword argument"
            for i,t in enumerate(targs):
                t.test(args[i])
            for k,t in tkwargs.items():
                t.test(kwargs[k])
            return func(*args, **kwargs)
        decorated.__dict__ = func.__dict__
        decorated.__verified__ = True
        decorated.__accepts__ = (targs, tkwargs)
        return decorated
    return decorator

def returns(returntype):
    t = TypeFactory(returntype)
    def decorator(func):
        assert not hasattr(func, "__returns__")
        def decorated(*args, **kwargs):
            retval = func(*args, **kwargs)
            t.test(retval)
            return retval
        decorated.__dict__ = func.__dict__
        decorated.__verified__ = True
        decorated.__returns__ = t
        return decorated
    return decorator
    
# def requires(condition):
#     def decorator(func):
#         c = compile(condition, "verifier", "exec")
#         def decorated(*args, **kwargs):
#             eval(c)

def test_function(func):
    assert hasattr(func, "__accepts__"), "No argument annotations"
    assert len(func.__accepts__[1]) == 0 # TODO kwargs
    for p in itertools.product(*[e.generate() for e in func.__accepts__[0]]):
        print(p)
        func(*p)

@accepts(Number(), Number())
@returns(Number())
def add(n, m):
    return n+m

add(4, 5)

test_function(add)
