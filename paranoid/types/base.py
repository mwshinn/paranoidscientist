__all__ = ['TypeFactory', 'Type', 'Constant', 'Unchecked', 'Generic',
           'Self', 'Nothing', 'Function', 'And', 'Or']

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
        super().__init__()
        assert const is not None, "None cannot be a constant"
        self.const = const
    def __repr__(self):
        return "Constant(%s)" % self.const
    def test(self, v):
        super().test(v)
        assert self.const == v
    def generate(self):
        yield self.const

class Unchecked(Type):
    """Use type `typ` but do not check it."""
    def __init__(self, typ):
        self.typ = TypeFactory(typ)
    def generate(self):
        for gv in self.typ.generate():
            yield gv

class Generic(Type):
    def __init__(self, typ):
        super().__init__()
        assert isinstance(typ, type)
        self.type = typ
    def test(self, v):
        assert isinstance(v, self.type)
        if hasattr(self.type, "_test") and callable(self.type._test):
            return self.type._test(v)
    def __repr__(self):
        return "Generic(%s)" % self.type
    def generate(self):
        if hasattr(self.type, "_generate") and callable(self.type._generate):
            for v in self.type._generate():
                yield v
        else:
            raise NoGeneratorError("Please define a _generate() function in "
                                   "class %s." % self.type.__name__)

class Self(Type):
    """Used only as a placeholder for methods with a 'self' argument."""
    def test(self, v):
        raise VerifyError("Invalid use of the Self type. (Did you forget to use @verifiedclass?)")
    def generate(self):
        raise VerifyError("Invalid use of the Self type. (Did you forget to use @verifiedclass?)")

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
                yield g

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
        if not any(v in t for t in self.types):
            raise AssertionError("Neither type in Or holds")
    def generate(self):
        ng = (e for t in self.types for e in t.generate())
        for g in ng:
            yield g
