# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

"""Unit tests for Paranoid Scientist.

Call using:

  $ python3 -m pytest tests.py
"""

import unittest
from unittest import TestCase, main
from paranoid.testfunctions import test_function as function_test
import paranoid.decorators as pd
import paranoid.types as pt
import paranoid.utils as pu
from paranoid.settings import Settings
from string import ascii_letters

def fails(f):
    failed = False
    try:
        f()
    except:
        failed = True
    if failed == False:
        raise ValueError("Error, function did not fail")

def identity_test(typ):
    @pd.accepts(typ)
    @pd.returns(typ)
    def f(x):
        return x
    # function_test returns the number of tests performed, so make
    # sure that we did at least one.
    assert function_test(f) > 0

def pair_test(acc, ret):
    @pd.accepts(acc)
    @pd.returns(ret)
    def f(x):
        return x
    # function_test returns the number of tests performed, so make
    # sure that we did at least one.
    assert function_test(f) > 0

def pair_fails(acc, ret):
    fails(lambda acc=acc,ret=ret : pair_test(acc, ret))

class TestTypes(TestCase):
    def setUp(self):
        self.numeric_types = [pt.Numeric, pt.ExtendedReal, pt.Number,
                              pt.Integer, pt.Natural0,
                              pt.RangeOpen(-1, 1.3),
                              pt.RangeClosedOpen(.4, 1.7),
                              pt.RangeOpenClosed(-7, -2),
                              pt.Range(0, 1), pt.Positive0, pt.Positive]
        self.string_types = [pt.String, pt.Identifier,
                             pt.Alphanumeric, pt.Latin]
    
    def test_numeric_types(self):
        """Types in the numeric module"""
        for t in self.numeric_types:
            identity_test(t)
        # Test some more ranges
        identity_test(pt.Range(-1, 1))
        identity_test(pt.Range(0, 10))
        identity_test(pt.Range(-.2, 3.1415))
        identity_test(pt.RangeClosedOpen(-1, 1))
        identity_test(pt.RangeClosedOpen(0, 10))
        identity_test(pt.RangeClosedOpen(-.2, 3.1415))
        identity_test(pt.RangeOpenClosed(-1, 1))
        identity_test(pt.RangeOpenClosed(0, 10))
        identity_test(pt.RangeOpenClosed(-.2, 3.1415))
        identity_test(pt.RangeOpen(-1, 1))
        identity_test(pt.RangeOpen(0, 10))
        identity_test(pt.RangeOpen(-.2, 3.1415))

        pair_test(pt.Natural1, pt.Natural0)

        pair_fails(pt.Numeric, pt.ExtendedReal)
        pair_fails(pt.Numeric, pt.Number)
        pair_fails(pt.Number, pt.Integer)
        pair_fails(pt.Integer, pt.Natural0)
        pair_fails(pt.Natural0, pt.Natural1)
        pair_fails(pt.Number, pt.Positive0)
        pair_fails(pt.Positive0, pt.Positive)
        pair_fails(pt.Range(0, 1), pt.RangeClosedOpen(0, 1))
        pair_fails(pt.Range(0, 1), pt.RangeOpenClosed(0, 1))
        pair_fails(pt.RangeOpenClosed(0, 1), pt.RangeOpen(0, 1))
        pair_fails(pt.RangeClosedOpen(0, 1), pt.RangeOpen(0, 1))
        pair_fails(pt.Range(0, 1), pt.Range(1, 2))
        
    def test_ndarray(self):
        """Numpy types"""
        typs = self.numeric_types + [None]
        dims = [1, 2, 3, None]
        for t in typs:
            for d in dims:
                identity_test(pt.NDArray(d=d, t=t))
    
    def test_string_types(self):
        """Types in the strings module"""
        for t in self.string_types:
            identity_test(t)

        pair_fails(pt.String, pt.Identifier)
        pair_fails(pt.Identifier, pt.Alphanumeric)
        pair_fails(pt.Alphanumeric, pt.Latin)
            
    def test_collection_types(self):
        """Types in the collections module"""
        alltypes = self.string_types + self.numeric_types
        for t in alltypes:
            identity_test(pt.List(t))
            identity_test(pt.Dict(k=pt.String, v=t))
            identity_test(pt.Dict(k=pt.Number, v=t))
            identity_test(pt.Tuple(pt.Number, t))
        identity_test(pt.Set(["a", "b", "c"]))
        identity_test(pt.Set([1.3, "abc", -1]))
        identity_test(pt.ParametersDict({}))
        identity_test(pt.ParametersDict({k : v for (k,v) in
                                         zip(ascii_letters, alltypes)}))
        identity_test(pt.Tuple(pt.Number))
        identity_test(pt.Tuple(pt.Number, pt.String, pt.Number))

    def test_TypeFactory(self):
        """Safely returning types using TypeFactory"""
        pair_test(pt.TypeFactory(pt.Integer), pt.TypeFactory(pt.Integer()))
        pair_test(None, pt.Nothing)
        assert 3 in pt.TypeFactory(int)
    
    def test_Constant(self):
        """Constants"""
        for c in [{}, [], "xyz", 123.45, True]:
            identity_test(pt.Constant(c))

    def test_Unchecked(self):
        """Unchecked function arguments"""
        alltypes = self.string_types + self.numeric_types
        for t1 in alltypes:
            for t2 in alltypes:
                pair_test(pt.Unchecked(t1), pt.Unchecked(t2))
            pair_test(pt.Unchecked(t1), pt.Unchecked)
        @pd.accepts(pt.Unchecked)
        @pd.returns(pt.Unchecked(t1))
        def f(x):
            return x
        assert function_test(f) == 0
        

    def test_Nothing(self):
        """Nothing type"""
        alltypes = self.string_types + self.numeric_types
        for t in alltypes:
            pair_fails(t, pt.Nothing)
            pair_fails(pt.Nothing, t)

    def test_Boolean(self):
        """Boolean type"""
        identity_test(pt.Boolean)
        pair_fails(123, pt.Boolean)

    def test_Function(self):
        """Function type"""
        assert (lambda x : x) in pt.Function()
        
    def test_And_Or_Not(self):
        """And, Or, and Not types"""
        identity_test(pt.And(pt.Natural0, pt.Range(0, 10)))
        identity_test(pt.Or(pt.Boolean, pt.Range(0, 10)))
        identity_test(pt.And(pt.Range(0, 10), pt.Not(pt.Range(3, 5))))
        identity_test(pt.And(pt.Range(0, 10), pt.Not(pt.Range(0, 5))))
    
    def test_class_type(self):
        """The Self variable and defining types from classes"""
        @pd.paranoidclass
        class MyClass:
            def __init__(self, val):
                self.val = val
            @staticmethod
            def _generate():
                yield MyClass(1)
                yield MyClass("string")
            @staticmethod
            def _test(v):
                v.val in pt.Integer()
            @pd.accepts(pt.Self)
            @pd.returns(pt.Self)
            def get_val(self):
                return self
        identity_test(MyClass)
        identity_test(pt.Generic(MyClass))
        assert function_test(MyClass.get_val) > 0
        pair_test(pt.TypeFactory(MyClass), pt.Generic(MyClass))

    def test_class_type_inheritance(self):
        """Test whether inherited methods properly resolve Self"""
        @pd.paranoidclass
        class MyClass:
            @pd.accepts(pt.Self)
            def f(self):
                pass
        @pd.paranoidclass
        class MyClassSub1(MyClass):
            @pd.accepts(pt.Self)
            def g(self):
                pass
        class MyClassSub2(MyClass):
            def g(self):
                pass
        #myclass = MyClass()
        #myclass.f()
        myclass_sub1 = MyClassSub1()
        myclass_sub1.f()
        myclass_sub1.g()
        myclass_sub2 = MyClassSub2()
        myclass_sub2.f()
        myclass_sub2.g()
        
class TestUtils(TestCase):
    def test_function_properties(self):
        """System for reading and writing function properties"""
        testfunc = lambda x : x
        assert not pu.has_fun_prop(testfunc, "pname")
        fails(lambda : pu.get_fun_prop(testfunc, "pname"))
        pu.set_fun_prop(testfunc, "pname", "testval")
        assert pu.has_fun_prop(testfunc, "pname")
        assert pu.get_fun_prop(testfunc, "pname") == "testval"

    def test_poskwarg_names(self):
        """Names of positional and keyword args"""
        def testfunc(a, b, *ars, **kwars):
            pass
        def testfunc2(a, b, c):
            pass
        assert pu.get_func_posargs_name(testfunc) == "ars"
        assert pu.get_func_kwargs_name(testfunc) == "kwars"
        assert pu.get_func_posargs_name(testfunc2) is None
        assert pu.get_func_kwargs_name(testfunc2) is None

class TestDecorators(TestCase):
    def test_requires(self):
        """Test the requires decorator"""
        @pd.requires("x > y")
        @pd.requires("x >= y")
        def simple(x, y):
            return 0
        assert simple(5, 3) == 0
        fails(lambda : simple(5, 5))
    def test_ensures(self):
        """Test the ensures decorator"""
        @pd.ensures("return > y")
        @pd.ensures("1 == 1")
        def simple(x, y):
            return x
        assert simple(5, 3) == 5
        fails(lambda : simple(5, 6))
    def test_ensures_implies(self):
        """Test implies --> notation"""
        @pd.ensures("y == 3 --> return == 1")
        def simple(x, y):
            return x
        assert simple(1, 3) == 1
        assert simple(1, 6) == 1
        assert simple(4, 2) == 4
        fails(lambda : simple(7, 3))
    def test_ensures_iff(self):
        """Test if and only if <--> notation"""
        @pd.ensures("y == 3 <--> return == 1")
        def simple(x, y):
            return x
        assert simple(1, 3) == 1
        fails(lambda : simple(1, 6))
        assert simple(4, 2) == 4
        fails(lambda : simple(7, 3))
    def test_ensures_backtick(self):
        """Test backtick notation for universal quantifier"""
        @pd.ensures("x > x` --> return > return`")
        def invert1(x):
            return -x
        invert1(3)
        fails(lambda : invert1(4))
        # Now the other way around
        @pd.ensures("x > x` --> return > return`")
        def invert2(x):
            return -x
        invert2(3)
        fails(lambda : invert2(2))
    def test_ensures_double_backtick(self):
        """Test double backtick notation for universal quantifier"""
        # Transitivity-like example
        @pd.ensures("x > x` and x` > x`` --> return > return``")
        @pd.paranoidconfig(max_cache=10)
        def quasitrans(x):
            return x if x != 3 else -3
        quasitrans(1)
        quasitrans(0)
        fails(lambda : quasitrans(3))
    def test_ensures_iter(self):
        """Make sure iterators work in requires/ensures conditions"""
        # There were formerly problems with iterators in conditions,
        # so this makes sure they won't pop up again.
        @pd.requires("all(x % 2 == 0 for x in l)")
        @pd.ensures("all(x > 0 for x in l)")
        def sumlist(l):
            return sum(l)
        assert sumlist([2, 4, 6]) == 12
        fails(lambda : sumlist([2, 3, 4]))
        fails(lambda : sumlist([3, 2, 1, 0]))
    def test_kwarg_only(self):
        """Test calling with keyword args only"""
        @pd.accepts(x=pt.Integer, y=pt.Number)
        def simple(**kwargs):
            return kwargs['x'] + kwargs['y']
        assert simple(x=5, y=3) == 8
        fails(lambda : simple(3, 5))
    def test_paranoidconfig(self):
        """Setting and reading config options"""
        @pd.paranoidconfig(enabled=False)
        @pd.accepts(pt.Boolean)
        @pd.returns(pt.Boolean)
        def not_boolean(x):
            return int(x + 3)
        not_boolean(5)
        # Flip the order so paranoidconfig is run first
        @pd.accepts(pt.Boolean)
        @pd.returns(pt.Boolean)
        @pd.paranoidconfig(enabled=False)
        def not_boolean(x):
            return int(x + 3)
        not_boolean(5)
        # Now make sure we can enable it again too
        @pd.paranoidconfig(enabled=True)
        @pd.accepts(pt.Boolean)
        @pd.returns(pt.Boolean)
        def not_boolean_fail(x):
            return int(x + 3)
        fails(lambda : not_boolean_fail(5))
    def test_with_other_decorator(self):
        """Compatibility of paranoid with other 3rd party decorators"""
        # Other decorator first
        from functools import lru_cache
        @lru_cache(maxsize=32)
        @pd.ensures("return > y")
        def simple(x, y):
            return x
        assert simple(5, 3) == 5
        fails(lambda : simple(5, 6))
        # Other decorator second
        # TODO this should work in theory but lru_cache doesn't copy properly
        # @pd.ensures("return > y")
        # @lru_cache(maxsize=32)
        # def simple(x, y):
        #     return x
        # assert simple(5, 3) == 5
        # fails(lambda : simple(5, 6))
        

class TestSettings(TestCase):
    def test_set_setting(self):
        """Assign a value to a setting"""
        # "enabled" is boolean
        prevval = Settings.get("enabled")
        Settings._set("enabled", not prevval)
        assert Settings.get("enabled") == (not prevval)
        Settings._set("enabled", prevval)
    def test_no_invalid_value(self):
        """Validation of settings values"""
        fails(lambda : Settings._set("enabled", 3))
        fails(lambda : Settings._set("max_cache", 3.1))
        fails(lambda : Settings._set("max_runtime", True))
    def test_set_setting_consistent(self):
        """Settings consistent when imported under different names"""
        import paranoid.settings as ps1
        import paranoid.settings as ps2
        from paranoid.settings import Settings as ps3
        prevval = ps1.Settings.get("max_cache")
        ps1.Settings._set("max_cache", 1234)
        assert ps2.Settings.get("max_cache") == 1234
        assert ps3.get("max_cache") == 1234
        ps1.Settings._set("max_cache", prevval)
    def test_function_local_override(self):
        """Functions can locally override global settings"""
        f1 = lambda x : x
        prevval = Settings.get("max_cache")
        Settings._set("max_cache", 1234)
        assert Settings.get("max_cache", function=f1) == 1234
        Settings._set("max_cache", 2345, function=f1)
        assert Settings.get("max_cache", function=f1) == 2345
        Settings._set("max_cache", prevval)
    def test_syntactic_sugar_set(self):
        """The nice interface to change settings is working"""
        prevval = Settings.get("enabled")
        Settings.set(enabled=False)
        assert Settings.get("enabled") == False
        Settings.set(enabled=True)
        assert Settings.get("enabled") == True
        Settings._set("enabled", prevval)
    def test_disable_paranoid(self):
        """Make sure we can disable paranoid scientist"""
        @pd.accepts(pt.Boolean)
        @pd.returns(pt.Boolean)
        def not_boolean(x):
            return int(x + 3)
        prevval = Settings.get("enabled")
        Settings.set(enabled=False)
        not_boolean(5)
        Settings.set(enabled=True)
        fails(lambda : not_boolean(5))
        Settings._set("enabled", prevval)
    def test_scoping_of_namespace(self):
        """Names in 'namespace' setting overridden by same-name argument"""
        Settings.get("namespace").update({"theval" : 3})
        @pd.accepts(theval=pt.Integer)
        @pd.ensures("theval != 3")
        def func(theval):
            pass
        func(2)
        fails(lambda : func(3))

if __name__ == '__main__':
    main()
