#!/usr/bin/python

import math

class Type():
    def test(self, v):
        pass

class Generic(Type):
    def __init__(self, t):
        assert isinstance(t, type)
        self.type = t
    def test(self, v):
        assert issubclass(type(v), self.type)

class Number(Type):
    def test(self, v):
        super().test(v)
        assert isinstance(v, (int, float)), "Invalid number"
        assert not math.isnan(v), "Number cannot be nan"

class Integer(Number):
    def test(self, v):
        super().test(v)
        assert v // 1 == v, "Invalid integer"

class Natural0(Integer):
    def test(self, v):
        super().test(v)
        assert v >= 0, "Must be greater than or equal to 0"

class Natural1(Natural0):
    def test(self, v):
        super().test(v)
        assert v > 0, "Must be greater than 0"

class Range(Number):
    def __init__(self, l, h):
        assert isinstance(l, (float, int)) and isinstance(h, (float, int)), "Invalid bounds"
        self.low = l if l is not None else -math.inf
        self.high = h if l is not None else math.inf
    def test(self, v):
        super().test(v)
        assert self.low <= v <= self.high

class Set(Type):
    def __init__(self, els):
        assert hasattr(els, "__contains__") and callable(els.__contains__)
        self.els = els
    def test(self, v):
        super().test(v)
        assert v in self.els, "Not in set"

class String(Type):
    def test(self, v):
        super().test(v)
        assert isinstance(v, str)

class List(Type):
    def __init__(self, t):
        self.type = t if issubclass(type(t), Type) else Generic(t)
    def test(self, v):
        super().test(v)
        assert isinstance(v, list)
        (self.type.test(e) for e in v)

class Dict(Type):
    def __init__(self, k, v):
        self.valtype = v if issubclass(type(v), Type) else Generic(v)
        self.keytype = k if issubclass(type(k), Type) else Generic(k)
    def test(self, v):
        super().test(v)
        assert isinstance(v, dict)
        for e in v.keys():
            self.keytype.test(e)
        for e in v.values():
            self.valtype.test(e)

def accepts(*argtypes, **kwargtypes):
    assert len(argtypes)+len(kwargtypes) > 0, "No arguments to accepts"
    def decorator(func):
        def decorated(*args, **kwargs):
            assert len(argtypes) == len(args), \
                "Invalid number of decorator arguments"
            assert all(k in kwargs.keys() for k in kwargtypes.keys()), \
                "Invalid decorator keyword argument"
            for i in range(len(argtypes)): # Known type
                t = argtypes[i] if issubclass(type(argtypes[i]), Type) else Generic(argtypes[i])
                t.test(args[i])
            return func(*args, **kwargs)
        return decorated
    return decorator

def returns(returntype):
    t = returntype if issubclass(type(returntype), Type) else Generic(returntype)
    def decorator(func):
        def decorated(*args, **kwargs):
            retval = func(*args, **kwargs)
            t.test(retval)
            return retval
        return decorated
    return decorator
    
# Tests
@accepts(Number())
@returns(Number())
def add_three(n):
    return n+3

add_three(4)
add_three(-10)
#add_three("hello")

@accepts(Number(), Number())
@returns(Number())
def add(n, m):
    return n+m

add(4, 5)

@accepts(Range(-1, 1))
@returns(Range(0, .9))
def square(n):
    return n*n

square(.3)
#square(.999)

@accepts(List(Integer()))
@returns(Integer())
def sumlist(l):
    return sum(l)

sumlist([3, 6, 2, 1])

@accepts(Dict(String(), Number()))
@returns(Dict(String(), Number()))
def ident(d):
    return d

ident({"a" : 3, "b" : 901.90})
#ident({"a" : "a", "b" : 901.90, "c" : 22})
#ident({"a" : 33, "b" : 901.90, 22 : 22})

class MyType:
    def __init__(self, val):
        self.val = val

@accepts(MyType)
@returns(MyType)
def myfun(mt):
    return MyType(3)

myfun(MyType(1))
#myfun("abc")
