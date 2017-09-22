#!/usr/bin/python

import math
import random
import itertools
import inspect
import functools
from exceptions import *

_FUN_PROPS = "__verify__"

def TypeFactory(v):
    if issubclass(type(v), Type):
        return v
    elif issubclass(v, Type):
        return v()
    elif issubclass(type(v), type):
        return Generic(v)
    else:
        raise InvalidTypeError("Invalid type %s" % v)

class Type():
    def test(self, v):
        pass

class Generic(Type):
    def __init__(self, typ):
        super().__init__()
        assert isinstance(typ, type)
        self.type = typ
    def test(self, v):
        assert isinstance(v, self.type)
    def generate(self):
        raise NoGeneratorError

class Nothing(Type):
    def test(self, v):
        assert v is None
    def generate(self):
        return [None]

class Numeric(Type):
    def test(self, v):
        super().test(v)
        assert isinstance(v, (int, float)), "Invalid numeric"
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
        assert low < high, "Low %s must be strictly greater than high %s" % (low, high)
        self.low = low if low is not None else -math.inf
        self.high = high if low is not None else math.inf
    def test(self, v):
        super().test(v)
        assert self.low <= v <= self.high, "Range must be greater than %f and less than %f" % (self.low, self.high)
    def _generate_quantiles(self):
        EPSILON = 1e-5
        if not (math.isinf(self.low) or math.isinf(self.high)):
            l = self.low
            h = self.high
            return [(l+h)*EPSILON, (l+h)*.5, (l+h)*.25, (l+h)*.75 (l+h)*(1-EPSILON)]
        elif math.isinf(self.low):
            return [self.high-EPSILON]
        elif math.isinf(self.high):
            return [self.low-EPSILON]
        raise AssertionError("Invalid Range bounds")
    def generate(self):
        return [self.low, self.high] + self._generate_quantiles()

class RangeClosedOpen(Range):
    def test(self, v):
        super().test(v)
        assert v != self.high, "Value must be strictly greater than %f" % self.high
    def generate(self):
        return [self.low] + self._generate_quantiles()

class RangeOpenClosed(Range):
    def test(self, v):
        super().test(v)
        assert v != self.low, "Value must be strictly less than %f" % self.low
    def generate(self):
        return [self.high] + self._generate_quantiles()

class RangeOpen(RangeClosedOpen, RangeOpenClosed):
    def test(self, v):
        super().test(v)
    def generate(self):
        return self._generate_quantiles()

class Set(Type):
    def __init__(self, els):
        super().__init__()
        assert hasattr(els, "__contains__") and callable(els.__contains__)
        self.els = els
    def test(self, v):
        super().test(v)
        assert v in self.els, "Value %v in set" % v
    def generate(self):
        return [e for e in self.els]

class String(Type):
    def test(self, v):
        super().test(v)
        assert isinstance(v, str), "Non-string passed"
    def generate(self):
        return ["", "a"*1000, "{100}", " ", "abc123", "two words", "\\", "%s", "1", "баклажан"]

class List(Type):
    def __init__(self, t):
        super().__init__()
        self.type = TypeFactory(t)
    def test(self, v):
        super().test(v)
        assert isinstance(v, list), "Non-list passed"
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
        assert isinstance(v, dict), "Non-dict passed"
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
            raise AssertionError("Neither type in Or holds")

def has_fun_prop(f, k):
    if not hasattr(f, _FUN_PROPS):
        return False
    if not isinstance(getattr(f, _FUN_PROPS), dict):
        return False
    if k not in getattr(f, _FUN_PROPS).keys():
        return False
    return True

def get_fun_prop(f, k):
    if not has_fun_prop(f, k):
        raise InternalError("Function %s has no property %s" % (str(f), k))
    return getattr(f, _FUN_PROPS)[k]

def set_fun_prop(f, k, v):
    if not hasattr(f, _FUN_PROPS):
        setattr(f, _FUN_PROPS, {})
    if not isinstance(getattr(f, _FUN_PROPS), dict):
        raise InternalError("Invalid function properties dictionary for %s" % str(f))
    getattr(f, _FUN_PROPS)[k] = v

def _decorator(func, argtypes=None, kwargtypes=None, returntype=None, requires=None, ensures=None):
    # @accepts decorator
    if argtypes is not None:
        argtypes = [TypeFactory(a) for a in argtypes]
        if has_fun_prop(func, "argtypes"):
            raise ValueError("Cannot set argument types twice")
        set_fun_prop(func, "argtypes", argtypes)
    if kwargtypes is not None:
        kwargtypes = {k : TypeFactory(a) for k,a in kwargtypes.items()}
        if has_fun_prop(func, "kwargtypes"):
            raise ValueError("Cannot set set keyword argument types twice")
        set_fun_prop(func, "kwargtypes", kwargtypes)
    # @returns decorator
    if returntype is not None:
        returntype = TypeFactory(returntype)
        if has_fun_prop(func, "returntype"):
            raise ValueError("Cannot set return type twice")
        set_fun_prop(func, "returntype", returntype)
    # @requires decorator
    if requires is not None:
        if has_fun_prop(func, "requires"):
            if not isinstance(get_fun_prop(func, "requires"), list):
                raise InternalError("Invalid requires structure")
            base_requires = get_fun_prop(func, "requires")
        else:
            base_requires = []
        set_fun_prop(func, "requires", [requires]+base_requires)
    # @ensures decorator
    if ensures is not None:
        if has_fun_prop(func, "ensures"):
            if not isinstance(get_fun_prop(func, "ensures"), list):
                raise InternalError("Invalid ensures strucutre")
            base_ensures = get_fun_prop(func, "ensures")
        else:
            base_ensures = []
        set_fun_prop(func, "ensures", [ensures]+base_ensures)
    def decorated(*args, **kwargs):
        # @accepts decorator
        if has_fun_prop(func, "argtypes") and has_fun_prop(func, "kwargtypes"):
            argtypes = get_fun_prop(func, "argtypes")
            kwargtypes = get_fun_prop(func, "kwargtypes")
            if argtypes:
                if len(argtypes) != len(args):
                    raise ArgumentTypeError("Invalid argument specification to @accepts")
                for i,t in enumerate(argtypes):
                    try:
                        t.test(args[i])
                    except AssertionError as e:
                        raise ArgumentTypeError("Invalid argument type %s" % args[i])
            if kwargtypes:
                if all(k in kwargs.keys() for k in kwargtypes.keys()):
                    raise ArgumentTypeError("Invalid keyword argument specification to @accepts")
                for k,t in kwargtypes.items():
                    try:
                        t.test(kwargs[k])
                    except AssertionError as e:
                        raise ArgumentTypeError("Invalid argument type for %s: %s" % (k, kwargs[k]))
        # @requires decorator
        if has_fun_prop(func, "requires"):
            argspec = inspect.getargspec(func)
            # Function named arguments
            #full_locals = locals().copy()
            #full_locals.update({k : v for k,v in zip(argspec.args, args)})
            full_locals = {k : v for k,v in zip(argspec.args, args)}
            # Unnamed positional arguments
            if argspec.varargs is not None:
                positional_args = {argspec.varargs: args[len(argspec.args):]}
                full_locals.update(positional_args)
            # TODO kw arguments
            for requirement in get_fun_prop(func, "requires"):
                if not eval(requirement, globals(), full_locals):
                    raise EntryConditionsError("Function requirement '%s' failed" % requirement)
        # The actual function
        returnvalue = func(*args, **kwargs)
        # @returns decorator
        if has_fun_prop(func, "returntype"):
            try:
                get_fun_prop(func, "returntype").test(returnvalue)
            except AssertionError as e:
                raise ReturnTypeError("Invalid return type of %s" % returnvalue )
        # @ensures decorator
        if has_fun_prop(func, "ensures"):
            argspec = inspect.getargspec(func)
            # Function named arguments
            limited_locals = {k : v for k,v in zip(argspec.args, args)}
            # Return value
            limited_locals['__RETURN__'] = returnvalue
            # Unnamed positional arguments
            if argspec.varargs is not None:
                positional_args = {argspec.varargs: args[len(argspec.args):]}
                limited_locals.update(positional_args)
            # TODO kw arguments
            for ensurement in get_fun_prop(func, "ensures"):
                e = ensurement.replace("return", "__RETURN__")
                if not eval(e, globals(), limited_locals):
                    raise ExitConditionsError("Ensures statement '%s' failed" % ensurement)
        return returnvalue
    # We have already wrapped this function
    if has_fun_prop(func, "active"):
        return func
    else:
        set_fun_prop(func, "active", True)
        assign = functools.WRAPPER_ASSIGNMENTS + (_FUN_PROPS,)
        return functools.wraps(func, assigned=assign)(decorated)


def accepts(*argtypes, **kwargtypes):
    return lambda f : _decorator(f, argtypes=argtypes, kwargtypes=kwargtypes)
def returns(returntype):
    return lambda f : _decorator(f, returntype=returntype)
def requires(condition):
    return lambda f : _decorator(f, requires=condition)
def ensures(condition):
    return lambda f : _decorator(f, ensures=condition)

def test_function(func):
    assert hasattr(func, _FUN_PROPS), "No argument annotations"
    for p in itertools.product(*[e.generate() for e in get_fun_prop(func, "argtypes")]):
        print(p)
        func(*p)

@accepts(Number(), Number())
@returns(Number())
#@requires("n < m")
@ensures("return == n + m")
@ensures("return >= m + n")
def add(n, m):
    return n+m

add(4, 5)
add(0, 5)

#test_function(add)
