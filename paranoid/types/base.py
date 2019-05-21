# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

__all__ = ['TypeFactory', 'Type', 'Constant', 'Unchecked', 'Generic',
           'InitGeneric', 'Self', 'Nothing', 'Function', 'Boolean',
           'And', 'Or', 'Not']

from ..exceptions import VerifyError, NoGeneratorError, InvalidTypeError
import inspect

def TypeFactory(v):
    """Ensure `v` is a valid Type.

    This function is used to convert user-specified types into
    internal types for the verification engine.  It allows Type
    subclasses, Type subclass instances, Python type, and user-defined
    classes to be passed.  Returns an instance of the type of `v`.

    Users should never access this function directly.
    """

    if v is None:
        return Nothing()
    elif issubclass(type(v), Type):
        return v
    elif isinstance(v, type) and issubclass(v, Type):
        return v()
    elif issubclass(type(v), type):
        return Generic(v)
    else:
        raise InvalidTypeError("Invalid type %s" % v)

class _MetaType(type):
    def __repr__(cls):
        return cls.__name__

class Type(metaclass=_MetaType):
    """The base Type, from which all variable types should inherit.

    What is a Type?  While "types" can include standard types built
    into the programming language (e.g. int, float, string), they can
    also be more flexible. For example, you can have a "natural
    numbers" type, or a "range" type, or even a "file path" type.

    All types must inherit from this class.  They must define the
    "test" and "generate" functions.
    """
    def __init__(self, *args, **kwargs):
        # Create the string representation
        pargs = [repr(v) for v in args]
        kargs = [k+"="+repr(v) for k,v in kwargs.items()]
        allargs = pargs+kargs
        self._repr = self.__class__.__name__
        if allargs:
            self._repr += "(%s)" % (", ".join(pargs+kargs))
        super().__init__()
    def __repr__(self):
        return self._repr
    def test(self, v):
        """Check whether `v` is a valid value of this type.  Throws an
        assertion error if `v` is not a valid value.
        """
        pass
    def generate(self):
        """Generate a list of values of this type."""
        raise NotImplementedError("Please subclass Type")
    def __contains__(self, v):
        try:
            self.test(v)
        except AssertionError:
            return False
        else:
            return True

class Constant(Type):
    """Only one valid value, which is passed at initialization"""
    def __init__(self, const):
        super().__init__(const=const)
        assert const is not None, "None cannot be a constant"
        self.const = const
    def __repr__(self):
        return "Constant(%s)" % repr(self.const)
    def test(self, v):
        super().test(v)
        assert self.const == v, "Invalid constant"
    def generate(self):
        yield self.const

class Unchecked(Type):
    """Use type `typ` but do not check it."""
    def __init__(self, typ=None):
        if typ is not None:
            self.typ = TypeFactory(typ)
            super().__init__(self.typ)
        else:
            self.typ = None
            super().__init__()
    def generate(self):
        if self.typ is not None:
            yield from self.typ.generate()

class Generic(Type):
    """Wraps Python classes to turn them into Types.

    Classes may optionally contain the "_test_(v)" or "_generate()"
    static methods; adding these two functions gives them the same
    power as traditional Types.  "_test(v)" should check if `v` is a
    valid member of the class using assert statements only, and
    "_generate()" should yield a finite number of instances of the class.
    """
    def __init__(self, typ):
        super().__init__(typ=typ)
        assert isinstance(typ, type)
        assert not isinstance(typ, Type), "Types don't need to be wrapped"
        self.type = typ
    def test(self, v):
        assert isinstance(v, self.type)
        type_and_parents = reversed(self.type.mro()[:-1]) # -1 removes <class 'object'>
        for t in type_and_parents:
            if hasattr(t, "_test") and callable(t._test):
                t._test(v)
    def __repr__(self):
        return "Generic(%s)" % self.type
    def generate(self):
        if hasattr(self.type, "_generate") and callable(self.type._generate):
            yield from self.type._generate()
        else:
            raise NoGeneratorError("Please define a _generate() function in "
                                   "class %s." % self.type.__name__)

class InitGeneric(Type):
    """For the self argument passed to __init__. Should not be used directly, use Self instead.

    Before a class is initialized (i.e. __init__ is called), it may
    not be valid according to its _test method.  Likewise, passing a
    fully initialized class value to __init__ through the self
    parameter may cause problems, as the self parameter for __init__
    is the output of the __new__ method.  Thus, the __init__ function
    must be handled separately.  This tests only object identity, and
    generates types based on the __new__ method.  This may fail for 

    """
    def __init__(self, typ):
        super().__init__(typ)
        assert isinstance(typ, type)
        assert not isinstance(typ, Type), "Types don't need to be wrapped"
        self.type = typ
    def test(self, v):
        assert isinstance(v, self.type)
    def generate(self):
        # We can't generate if the __new__ method takes arguments
        nargs = len(inspect.getfullargspec(self.type.__new__).args)
        if nargs == 1:
            # __new__ automatically calls __init__, so set __init__ to
            # an empty function to temporarily avoid calling it
            init = self.type.__init__
            self.type.__init__ = lambda *args, **kwargs: None
            obj = self.type.__new__(self.type)
            self.type.__init__ = init
            yield obj
    

class Self(Type):
    """Used only as a placeholder for methods with a 'self' argument."""
    def test(self, v):
        raise VerifyError("Invalid use of the Self type. (Did you forget to use @paranoidclass?)")
    def generate(self):
        raise VerifyError("Invalid use of the Self type. (Did you forget to use @paranoidclass?)")

class Nothing(Type):
    """The None type."""
    def test(self, v):
        assert v is None
    def generate(self):
        yield None

# TODO expand this to define argument/return types
class Function(Type):
    """Any function."""
    def test(self, v):
        super().test(v)
        assert callable(v), "Not a function"
    def generate(self):
        raise NoGeneratorError

class Boolean(Type):
    """True or False"""
    def test(self, v):
        super().test(v)
        assert v in [True, False], "Not a boolean"
    def generate(self):
        yield True
        yield False

class And(Type):
    """Conforms to all of the given types.

    Any number of Types can be passed to And.  The And of these types
    is the logical AND of them, i.e. a value must conform to each of
    the types.
    """
    def __init__(self, *types):
        self.types = [TypeFactory(a) for a in types]
        super().__init__(*self.types)
    def test(self, v):
        for t in self.types:
            t.test(v)
    def generate(self):
        all_generated = [e for t in self.types for e in t.generate() or []]
        valid_generated = []
        for g in all_generated:
            try:
                for t in self.types:
                    t.test(g)
            except AssertionError:
                continue
            else:
                yield g

class Or(Type):
    """Conforms to any of the given types.

    Any number of Types can be passed to Or.  The Or of these types is
    the logical OR of them, i.e. a value must conform to at least one
    the types.
    """
    def __init__(self, *types):
        self.types = [TypeFactory(a) for a in types]
        super().__init__(*self.types)
    def test(self, v):
        passed = False
        if not any(v in t for t in self.types):
            raise AssertionError("Neither type in Or holds")
    def generate(self):
        ng = (e for t in self.types for e in t.generate())
        for g in ng:
            yield g

class Not(Type):
    """Valid if the given type fails.

    Takes one type as an argument.  Valid values are not of this type.

    Note that this should be avoided when possible, as it cannot
    generate values.  It is most useful within an And clause.
    """
    def __init__(self, typ):
        super().__init__(typ)
        self.type = TypeFactory(typ)
    def test(self, v):
        assert not (v in self.type), "Not clause does not hold"
    def generate(self):
        pass

class PositionalArguments(Type):
    """Function optional positional arguments.

    This is used internally.
    """
    def test(self, v):
        super().test(v)
        assert isinstance(v, tuple), "Non-dict passed"
    def generate(self):
        yield ()


class KeywordArguments(Type):
    """Function optional keyword arguments.

    This is used internally.
    """
    def test(self, v):
        super().test(v)
        assert isinstance(v, dict), "Non-dict passed"
        for e in v.keys():
            isinstance(e, str)
    def generate(self):
        yield {}


