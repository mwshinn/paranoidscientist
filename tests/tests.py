import unittest
from unittest import TestCase, main
from paranoid.testfunctions import test_function
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

def test_identity(typ):
    @pd.accepts(typ)
    @pd.returns(typ)
    def f(x):
        return x
    # test_function returns the number of tests performed, so make
    # sure that we did at least one.
    assert test_function(f) > 0

def test_pair(acc, ret):
    @pd.accepts(acc)
    @pd.returns(ret)
    def f(x):
        return x
    # test_function returns the number of tests performed, so make
    # sure that we did at least one.
    assert test_function(f) > 0

def pair_fails(acc, ret):
    fails(lambda acc=acc,ret=ret : test_pair(acc, ret))

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
        for t in self.numeric_types:
            test_identity(t)
        # Test some more ranges
        test_identity(pt.Range(-1, 1))
        test_identity(pt.Range(0, 10))
        test_identity(pt.Range(-.2, 3.1415))
        test_identity(pt.RangeClosedOpen(-1, 1))
        test_identity(pt.RangeClosedOpen(0, 10))
        test_identity(pt.RangeClosedOpen(-.2, 3.1415))
        test_identity(pt.RangeOpenClosed(-1, 1))
        test_identity(pt.RangeOpenClosed(0, 10))
        test_identity(pt.RangeOpenClosed(-.2, 3.1415))
        test_identity(pt.RangeOpen(-1, 1))
        test_identity(pt.RangeOpen(0, 10))
        test_identity(pt.RangeOpen(-.2, 3.1415))

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
        typs = self.numeric_types + [None]
        dims = [1, 2, 3, None]
        for t in typs:
            for d in dims:
                test_identity(pt.NDArray(d=d, t=t))
    
    def test_string_types(self):
        for t in self.string_types:
            test_identity(t)

        pair_fails(pt.String, pt.Identifier)
        pair_fails(pt.Identifier, pt.Alphanumeric)
        pair_fails(pt.Alphanumeric, pt.Latin)
            
    def test_collection_types(self):
        alltypes = self.string_types + self.numeric_types
        for t in alltypes:
            test_identity(pt.List(t))
            test_identity(pt.Dict(k=pt.String, v=t))
            test_identity(pt.Dict(k=pt.Number, v=t))
        test_identity(pt.Set(["a", "b", "c"]))
        test_identity(pt.Set([1.3, "abc", -1]))
        test_identity(pt.ParametersDict({}))
        test_identity(pt.ParametersDict({k : v for (k,v) in
                                         zip(ascii_letters, alltypes)}))

    def test_TypeFactory(self):
        test_pair(pt.TypeFactory(pt.Integer), pt.TypeFactory(pt.Integer()))
        test_pair(None, pt.Nothing)
        assert 3 in pt.TypeFactory(int)
    
    def test_Constant(self):
        for c in [{}, [], "xyz", 123.45, True]:
            test_identity(pt.Constant(c))

    def test_Unchecked(self):
        alltypes = self.string_types + self.numeric_types
        for t1 in alltypes:
            for t2 in alltypes:
                test_pair(pt.Unchecked(t1), pt.Unchecked(t2))

    def test_Nothing(self):
        alltypes = self.string_types + self.numeric_types
        for t in alltypes:
            pair_fails(t, pt.Nothing)
            pair_fails(pt.Nothing, t)

    def test_Boolean(self):
        test_identity(pt.Boolean)
        pair_fails(123, pt.Boolean)

    def test_Function(self):
        assert (lambda x : x) in pt.Function()
        
    def test_And_Or_Not(self):
        test_identity(pt.And(pt.Natural0, pt.Range(0, 10)))
        test_identity(pt.Or(pt.Boolean, pt.Range(0, 10)))
        test_identity(pt.And(pt.Range(0, 10), pt.Not(pt.Range(3, 5))))
        test_identity(pt.And(pt.Range(0, 10), pt.Not(pt.Range(0, 5))))
    
    def test_class_type(self):
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
            def get_val(self):
                return self.val
        test_identity(MyClass)
        test_identity(pt.Generic(MyClass))
        assert test_function(MyClass.get_val) > 0
        test_pair(pt.TypeFactory(MyClass), pt.Generic(MyClass))

class TestUtils(TestCase):
    def test_function_properties(self):
        testfunc = lambda x : x
        assert not pu.has_fun_prop(testfunc, "pname")
        fails(lambda : pu.get_fun_prop(testfunc, "pname"))
        pu.set_fun_prop(testfunc, "pname", "testval")
        assert pu.has_fun_prop(testfunc, "pname")
        assert pu.get_fun_prop(testfunc, "pname") == "testval"

    def test_poskwarg_names(self):
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
        @pd.requires("x > y")
        def simple(x, y):
            return 0
        assert simple(5, 3) == 0
        fails(lambda : simple(5, 5))
    def test_ensures(self):
        @pd.ensures("return > y")
        def simple(x, y):
            return x
        assert simple(5, 3) == 5
        fails(lambda : simple(5, 6))
    def test_ensures_implies(self):
        @pd.ensures("y == 3 --> return == 1")
        def simple(x, y):
            return x
        assert simple(1, 3) == 1
        assert simple(1, 6) == 1
        assert simple(4, 2) == 4
        fails(lambda : simple(7, 3))
    def test_ensures_iff(self):
        @pd.ensures("y == 3 <--> return == 1")
        def simple(x, y):
            return x
        assert simple(1, 3) == 1
        fails(lambda : simple(1, 6))
        assert simple(4, 2) == 4
        fails(lambda : simple(7, 3))
    def test_ensures_backtick(self):
        @pd.ensures("x > x` --> return > return`")
        def invert1(x):
            return -x
        invert1(3)
        fails(lambda : invert1(4))
        # # TODO in theory I suppose this should work.
        # @pd.ensures("x > x` --> return > return`")
        # def invert2(x):
        #     return -x
        # invert2(3)
        # fails(lambda : invert2(2))
    def test_ensures_iter(self):
        # There were formerly problems with iterators in conditions,
        # so this makes sure they won't pop up again.
        @pd.requires("all(x % 2 == 0 for x in l)")
        @pd.ensures("all(x > 0 for x in l)")
        def sumlist(l):
            return sum(l)
        assert sumlist([2, 4, 6]) == 12
        fails(lambda : sumlist([2, 3, 4]))
        fails(lambda : sumlist([3, 2, 1, 0]))
    def test_paranoidconfig(self):
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
        # "enabled" is boolean
        prevval = Settings.get("enabled")
        Settings._set("enabled", not prevval)
        assert Settings.get("enabled") == (not prevval)
        Settings._set("enabled", prevval)
    def test_no_invalid_value(self):
        fails(lambda : Settings._set("enabled", 3))
        fails(lambda : Settings._set("max_cache", 3.1))
        fails(lambda : Settings._set("max_runtime", True))
    def test_set_setting_consistent(self):
        import paranoid.settings as ps1
        import paranoid.settings as ps2
        from paranoid.settings import Settings as ps3
        prevval = ps1.Settings.get("max_cache")
        ps1.Settings._set("max_cache", 1234)
        assert ps2.Settings.get("max_cache") == 1234
        assert ps3.get("max_cache") == 1234
        ps1.Settings._set("max_cache", prevval)
    def test_function_local_override(self):
        f1 = lambda x : x
        prevval = Settings.get("max_cache")
        Settings._set("max_cache", 1234)
        assert Settings.get("max_cache", function=f1) == 1234
        Settings._set("max_cache", 2345, function=f1)
        assert Settings.get("max_cache", function=f1) == 2345
        Settings._set("max_cache", prevval)
    def test_syntactic_sugar_set(self):
        prevval = Settings.get("enabled")
        Settings.set(enabled=False)
        assert Settings.get("enabled") == False
        Settings.set(enabled=True)
        assert Settings.get("enabled") == True
        Settings._set("enabled", prevval)
    def test_disable_paranoid(self):
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

if __name__ == '__main__':
    main()
