#!/usr/bin/python

import sys
import math
import itertools
import inspect
import functools
from exceptions import *

_FUN_PROPS = "__verify__"

def TypeFactory(v):
    """Ensure `v` is a valid Type.

    This function is used to convert user-specified types into
    internal types for the verification engine.  It allows Type
    subclasses, Type subclass instances, Python type, and user-defined
    classes to be passed.  Returns an instance of the type of `v`.

    Users should never access this function directly.
    """

    if issubclass(type(v), Type):
        return v
    elif issubclass(v, Type):
        return v()
    elif issubclass(type(v), type):
        return Generic(v)
    elif v is None:
        return Nothing()
    else:
        raise InvalidTypeError("Invalid type %s" % v)

class Type():
    """The base Type, from which all variable types should inherit.

    What is a Type?  While "types" can include standard types built
    into the programming language (e.g. int, float, string), they can
    also be more flexible. For example, you can have a "natural
    numbers" type, or a "range" type, or even a "file path" type.

    All types must inherit from this class.  They must define the
    "test" and "generate" functions.
    """
    def test(self, v):
        """Check whether `v` is a valid value of this type.  Throws an
        assertion error if `v` is not a valid value.
        """
        pass
    def generate(self):
        """Generate a list of values of this type."""
        raise NotImplementedError("Please subclass Type")

class Generic(Type):
    def __init__(self, typ):
        super().__init__()
        assert isinstance(typ, type)
        self.type = typ
    def test(self, v):
        assert isinstance(v, self.type)
        if hasattr(self.type, "_test") and callable(self.type._test):
            return self.type._test(v)
    def generate(self):
        if hasattr(self.type, "_generate") and callable(self.type._generate):
            return self.type._generate()
        else:
            raise NoGeneratorError("Please define a _generate() function in "
                                   "class %s." % self.type.__name__)

class Nothing(Type):
    """The None type."""
    def test(self, v):
        assert v is None
    def generate(self):
        return [None]

class Numeric(Type):
    """Any integer or float, including inf, -inf, and nan."""
    def test(self, v):
        super().test(v)
        assert isinstance(v, (int, float)), "Invalid numeric"
    def generate(self):
        # Check infinity, nan, 0, +/- numbers, a float, a small/big number
        return [math.inf, -math.inf, math.nan, 0, 1, -1, 3.141, 1e-10, 1e10]

class Number(Numeric):
    """Any integer or float, excluding inf, -inf, and nan."""
    def test(self, v):
        super().test(v)
        assert isinstance(v, (int, float)), "Invalid number"
        assert not math.isnan(v), "Number cannot be nan"
        assert not math.isinf(v), "Number must be finite"
    def generate(self):
        return [0, 1, -1, 3.141, 1e-10, 1e10]

class Integer(Number):
    """Any integer."""
    def test(self, v):
        super().test(v)
        assert v // 1 == v, "Invalid integer"
    def generate(self):
        return [-100, -1, 0, 1, 100]

class Natural0(Integer):
    """Any natural number including 0."""
    def test(self, v):
        super().test(v)
        assert v >= 0, "Must be greater than or equal to 0"
    def generate(self):
        return [0, 1, 10, 100]

class Natural1(Natural0):
    """Any natural number excluding 0."""
    def test(self, v):
        super().test(v)
        assert v > 0, "Must be greater than 0"
    def generate(self):
        return [1, 2, 10, 100]

class Range(Number):
    """Any integer or float from `low` to `high`, inclusive."""
    def __init__(self, low, high):
        super().__init__()
        assert isinstance(low, (float, int)) and \
            isinstance(high, (float, int)), "Invalid bounds"
        assert low < high, \
            "Low %s must be strictly greater than high %s" % (low, high)
        self.low = low if low is not None else -math.inf
        self.high = high if low is not None else math.inf
    def test(self, v):
        super().test(v)
        assert self.low <= v <= self.high, "Value %f must be greater" \
            "than %f and less than %f" % (v, self.low, self.high)
    def _generate_quantiles(self):
        EPSILON = 1e-5
        if not (math.isinf(self.low) or math.isinf(self.high)):
            l = self.low
            h = self.high
            return [(l+h)*EPSILON, (l+h)*.5, (l+h)*.25, (l+h)*.75, (l+h)*(1-EPSILON)]
        elif math.isinf(self.low):
            return [self.high-EPSILON]
        elif math.isinf(self.high):
            return [self.low-EPSILON]
        raise AssertionError("Invalid Range bounds")
    def generate(self):
        return [self.low, self.high] + self._generate_quantiles()

class RangeClosedOpen(Range):
    """A half open interval from `low` (closed) to `high` (open)."""
    def test(self, v):
        super().test(v)
        assert v != self.high, "Value must be strictly greater than %f" % self.high
    def generate(self):
        return [self.low] + self._generate_quantiles()

class RangeOpenClosed(Range):
    """A half open interval from `low` (open) to `high` (closed)."""
    def test(self, v):
        super().test(v)
        assert v != self.low, "Value must be strictly less than %f" % self.low
    def generate(self):
        return [self.high] + self._generate_quantiles()

class RangeOpen(RangeClosedOpen, RangeOpenClosed):
    """Any number in the open interval from `low` to `high`."""
    def test(self, v):
        super().test(v)
    def generate(self):
        return self._generate_quantiles()

class Set(Type):
    """Any element which is a member of `els`.

    `els` can be one of several standard Python types, including a
    list, a tuple, or a set.  Any object with the __contains__
    function is valid.  This ensures that a value is contained within
    `els`.
    """
    def __init__(self, els):
        super().__init__()
        assert hasattr(els, "__contains__") and callable(els.__contains__)
        self.els = els
    def test(self, v):
        super().test(v)
        assert v in self.els, "Value %s in set" % v
    def generate(self):
        return [e for e in self.els]

class String(Type):
    """Any string."""
    def test(self, v):
        super().test(v)
        assert isinstance(v, str), "Non-string passed"
    def generate(self):
        return ["", "a"*1000, "{100}", " ", "abc123", "two words", "\\", "%s", "1", "баклажан"]

class List(Type):
    """A Python list."""
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
    """A Python dictionary."""
    def __init__(self, k, v):
        super().__init__()
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
    """Conforms to all of the given types.

    Any number of Types can be passed to And.  The And of these types
    is the logical AND of them, i.e. a value must conform to each of
    the types.
    """
    def __init__(self, *types):
        super().__init__()
        self.types = [TypeFactory(a) for a in types]
    def test(self, v):
        for t in self.types:
            t.test(v)
    def generate(self):
        all_generated = [e for t in self.types for e in t.generate()]
        valid_generated = []
        for g in all_generated:
            try:
                for t in self.types:
                    t.test(g)
            except AssertionError:
                continue
            else:
                valid_generated.append(g)
        return valid_generated

class Or(Type):
    """Conforms to any of the given types.

    Any number of Types can be passed to Or.  The Or of these types is
    the logical OR of them, i.e. a value must conform to at least one
    the types.
    """
    def __init__(self, *types):
        super().__init__()
        self.types = [TypeFactory(a) for a in types]
    def test(self, v):
        passed = False
        for t in self.types:
            try:
                t.test(v)
                passed = True
            except AssertionError:
                continue
        if not passed:
            raise AssertionError("Neither type in Or holds")
    def generate(self):
        return [e for t in self.types for e in t.generate()]

def has_fun_prop(f, k):
    """Test whether function `f` has property `k`.

    We define properties as annotations added to a function throughout
    the process of defining a function for verification, e.g. the
    argument types.  If `f` is an unannotated function, this returns
    False.  If `f` has the property named `k`, it returns True.
    Otherwise, it returns False.

    Users should never access this function directly.
    """
    if not hasattr(f, _FUN_PROPS):
        return False
    if not isinstance(getattr(f, _FUN_PROPS), dict):
        return False
    if k not in getattr(f, _FUN_PROPS).keys():
        return False
    return True

def get_fun_prop(f, k):
    """Get the value of property `k` from function `f`.

    We define properties as annotations added to a function throughout
    the process of defining a function for verification, e.g. the
    argument types.  If `f` does not have a property named `k`, this
    throws an error.  If `f` has the property named `k`, it returns
    the value of it.

    Users should never access this function directly.
    """
    if not has_fun_prop(f, k):
        raise InternalError("Function %s has no property %s" % (str(f), k))
    return getattr(f, _FUN_PROPS)[k]

def set_fun_prop(f, k, v):
    """Set the value of property `k` to be `v` in function `f`.

    We define properties as annotations added to a function throughout
    the process of defining a function for verification, e.g. the
    argument types.  This sets function `f`'s property named `k` to be
    value `v`.

    Users should never access this function directly.
    """
    if not hasattr(f, _FUN_PROPS):
        setattr(f, _FUN_PROPS, {})
    if not isinstance(getattr(f, _FUN_PROPS), dict):
        raise InternalError("Invalid function properties dictionary for %s" % str(f))
    getattr(f, _FUN_PROPS)[k] = v

def _wrap(func):
    def _decorated(*args, **kwargs):
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
            if any("`" in ens for ens in get_fun_prop(func, "ensures")) : # Cache if we refer to previous executions
                if has_fun_prop(func, "exec_cache"):
                    exec_cache = get_fun_prop(func, "exec_cache")
                else:
                    exec_cache = []
                exec_cache.append(limited_locals.copy())
                set_fun_prop(func, "exec_cache", exec_cache) #TODO is this line necessary?
            # TODO kw arguments
            for ensurement in get_fun_prop(func, "ensures"):
                e = ensurement.replace("return", "__RETURN__")
                if "<-->" in e:
                    e_parts = e.split("<-->")
                    assert len(e_parts) == 2, "Only one implies per statement"
                    e = "((%s) if (%s) else True) and ((%s) if (%s) else True)" % (e_parts[1], e_parts[0], e_parts[0], e_parts[1])
                if "-->" in e: # TODO won't throw error if --> and <--> are in e
                    e_parts = e.split("-->")
                    assert len(e_parts) == 2, "Only one implies per statement"
                    e = "(%s) if (%s) else True" % (e_parts[1], e_parts[0])
                if "`" in e:
                    bt = "__BACKTICK__"
                    exec_cache = get_fun_prop(func, "exec_cache")
                    for cache_item in exec_cache:
                        limited_locals.update({k+bt : v for k,v in cache_item.items()})
                        e = e.replace("`", bt)
                        if not eval(e, globals(), limited_locals):
                            raise ExitConditionsError("Ensures statement '%s' failed" % ensurement)
                elif not eval(e, globals(), limited_locals):
                    raise ExitConditionsError("Ensures statement '%s' failed" % ensurement)
        return returnvalue
    if has_fun_prop(func, "active"):
        return func
    else:
        set_fun_prop(func, "active", True)
        assign = functools.WRAPPER_ASSIGNMENTS + (_FUN_PROPS,)
        wrapped = functools.wraps(func, assigned=assign)(_decorated)
        if "__ALL_FUNCTIONS" in globals().keys():
            __ALL_FUNCTIONS.append(wrapped)
        return wrapped
    

def accepts(*argtypes, **kwargtypes):
    argtypes = [TypeFactory(a) for a in argtypes]
    kwargtypes = {k : TypeFactory(a) for k,a in kwargtypes.items()}
    def _decorator(func):
        # @accepts decorator
        if argtypes is not None:
            if has_fun_prop(func, "argtypes"):
                raise ValueError("Cannot set argument types twice")
            set_fun_prop(func, "argtypes", argtypes)
        if kwargtypes is not None:
            if has_fun_prop(func, "kwargtypes"):
                raise ValueError("Cannot set set keyword argument types twice")
            set_fun_prop(func, "kwargtypes", kwargtypes)
        return _wrap(func)
    return _decorator

def returns(returntype):
    returntype = TypeFactory(returntype)
    def _decorator(func):
        # @returns decorator
        if has_fun_prop(func, "returntype"):
            raise ValueError("Cannot set return type twice")
        set_fun_prop(func, "returntype", returntype)
        return _wrap(func)
    return _decorator
            
def requires(condition):
    def _decorator(func):
        # @requires decorator
        if has_fun_prop(func, "requires"):
            if not isinstance(get_fun_prop(func, "requires"), list):
                raise InternalError("Invalid requires structure")
            base_requires = get_fun_prop(func, "requires")
        else:
            base_requires = []
        set_fun_prop(func, "requires", [condition]+base_requires)
        return _wrap(func)
    return _decorator

def ensures(condition):
    def _decorator(func):
    # @ensures decorator
        if has_fun_prop(func, "ensures"):
            if not isinstance(get_fun_prop(func, "ensures"), list):
                raise InternalError("Invalid ensures strucutre")
            base_ensures = get_fun_prop(func, "ensures")
        else:
            base_ensures = []
        set_fun_prop(func, "ensures", [condition]+base_ensures)
        return _wrap(func)
    return _decorator

def test_function(func):
    """Perform a unit test of a single function.

    Create a series of test cases by finding the type of each of the
    function arguments, and creating all possible combinations of test
    cases for each type using the type's generate() function.  Then,
    test the function with each input.  This is roughly equivalent to
    just running the function with each input, because the exceptions
    should be caught at runtime.

    Assuming runtime checking is enabled (as it should be), running
    this on a function only tests it for inputs it is likely to
    encounter in the future.
    """
    # Ensure the user has specified argument types using the @accepts
    # decorator.
    assert has_fun_prop(func, "argtypes"), "No argument annotations"
    # Generate all combinations of arguments as test cases.  Some
    # argument types cannot be generated automatically.  If we
    # encounter one of these, unit testing won't work.
    try:
        testcases = itertools.product(*[e.generate() for e in get_fun_prop(func, "argtypes")])
    except NoGeneratorError:
        testcases = []
    if not testcases:
        print("Warning: %s could not be tested" % func.__name__)
        return
    # If entry conditions are met, simply running the function will be
    # enough of a test, since all values are checked at runtime.  So
    # execute the function once for each combination of arguments.
    for tc in testcases:
        try:
            func(*tc)
        except EntryConditionsError:
            continue

# If called as "python3 -m verify script_file_name.py", then unit test
# script_file_name.py.  By this, we mean call the function
# test_function on each function which has annotations.  Note that we
# must execute the entire file script_file_name.py in order to do
# this, so any time-intensive code should be in a __name__ ==
# "__main__" guard, which will not be executed.
#
# We know if a function has annotations because all annotations are
# passed through the _decorator function (so that we can ensure we
# only use at most one more stack frame no matter how many function
# annotations we have).  The _decorator function will look for the
# global variable __ALL_FUNCTIONS to be defined within the verify
# module.  If it is defined, it will add one copy of each decorated
# function to the list.  Then, we can perform the unit test by
# iterating through each of these.  This has the advantage of allowing
# nested functions and object methods to be discovered for
# verification.
if __name__ == "__main__":
    # Pass exactly one argement: the python file to check
    if len(sys.argv) != 2: # len == 2 because the path to the module is arg 1.
        exit("Invalid argument, please pass a python file")
    # Add the __ALL_FUNCTIONS to the global scope of the verify module
    # and then run the script.  Save the global variables from script
    # execution so that we can find the __ALL_FUNCTIONS variable once
    # the script has finished executing.
    globs = {} # Global variables from script execution
    prefix = "import verify as __verifymod\n__verifymod.__ALL_FUNCTIONS = []\n"
    exec(prefix+open(sys.argv[1], "r").read(), globs)
    all_functions = globs["__verifymod"].__ALL_FUNCTIONS
    # Test each function from the script.
    for f in all_functions:
        assert hasattr(f, _FUN_PROPS), "Internal error"
        # Some function executions might take a while, so we print to
        # the screen when we begin testing a function, and then erase
        # it after we finish testing the function.  This is like a
        # make-shift progress bar.
        start_text = "    Testing %s..." % f.__name__
        print(start_text, end="", flush=True)
        test_function(f)
        # Extra spaces after "Tested %s" compensate for the fact that
        # the string to signal the start of testing function f is
        # longer than the string to signal function f has been tested,
        # so this avoids leaving extra characters on the terminal.
        print("\b"*len(start_text)+"    Tested %s    " % f.__name__, flush=True)
    print("Tested %i functions in %s." % (len(all_functions), sys.argv[1]))
