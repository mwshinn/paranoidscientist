__all__ = ['accepts', 'requires', 'returns', 'ensures', 'immutable_argument', 'verifiedclass']
import functools
from copy import deepcopy
from .util import has_fun_prop, set_fun_prop, get_fun_prop, test_equality, _FUN_PROPS
from .types.base import TypeFactory, Type, Constant, Self, Generic
from .exceptions import *
import inspect

def _wrap(func):
    def _decorated(*args, **kwargs):
        # @accepts decorator
        if has_fun_prop(func, "argtypes"):
            argtypes = get_fun_prop(func, "argtypes")
            argvals = inspect.getcallargs(func, *args, **kwargs)
            if sorted(argtypes.keys()) != sorted(argvals.keys()):
                raise ArgumentTypeError("Invalid argument specification in %s" % func.__name__)
            for k in argtypes.keys():
                try:
                    argtypes[k].test(argvals[k])
                except AssertionError as e:
                    raise ArgumentTypeError("Invalid argument type: %s=%s is not of type %s in %s" % (k, argvals[k], argtypes[k], func.__name__))
        # @requires decorator
        if has_fun_prop(func, "requires"):
            argvals = inspect.getcallargs(func, *args, **kwargs)
            # Function named arguments
            #full_locals = locals().copy()
            #full_locals.update({k : v for k,v in zip(argspec.args, args)})
            full_locals = argvals
            for requirement in get_fun_prop(func, "requires"):
                if not eval(requirement, globals(), full_locals):
                    raise EntryConditionsError("Function requirement '%s' failed in %s" % (requirement,  func.__name__))
        # Function argument comparison: Allow testing for function
        # arguments which were modified.  To do so, first save an
        # extra copy of the testcase.
        if has_fun_prop(func, "immutable_argument"):
            prev_args = deepcopy(args)
            prev_kwargs = deepcopy(kwargs)
        # The actual function
        returnvalue = func(*args, **kwargs)
        # @returns decorator
        if has_fun_prop(func, "returntype"):
            try:
                get_fun_prop(func, "returntype").test(returnvalue)
            except AssertionError as e:
                raise ReturnTypeError("Invalid return type of %s in %s" % (returnvalue, func.__name__) )
        # Function argument comparison: To finish comparing arguments,
        # test the arguments for equality.  We cannot check for simple
        # equality because many objects have identity equality
        # built-in, so testing from a deepcopy is guaranteed to fail,
        # i.e. deepcopy(a) != a.  So, if the argument has a __dict__
        # property, we try comparing that.  Otherwise, we compare the
        # value.
        if has_fun_prop(func, "immutable_argument"):
            for a1,a2 in zip(prev_args,args):
                if not test_equality(a1, a2):
                    raise ObjectModifiedError
            for k in kwargs.keys():
                if not test_equality(prev_kwargs[k], kwargs[k]):
                    raise ObjectModifiedError
        # @ensures decorator
        if has_fun_prop(func, "ensures"):
            argtypes = get_fun_prop(func, "argtypes")
            argvals = inspect.getcallargs(func, *args, **kwargs)
            # Function named arguments
            limited_locals = argvals
            # Return value
            limited_locals['__RETURN__'] = returnvalue
            if any("`" in ens for ens in get_fun_prop(func, "ensures")) : # Cache if we refer to previous executions
                if has_fun_prop(func, "exec_cache"):
                    exec_cache = get_fun_prop(func, "exec_cache")
                else:
                    exec_cache = []
                    set_fun_prop(func, "exec_cache", exec_cache)
                exec_cache.append(limited_locals.copy())
            for ensurement in get_fun_prop(func, "ensures"):
                e = ensurement.replace("return", "__RETURN__")
                if "<-->" in e:
                    e_parts = e.split("<-->")
                    assert len(e_parts) == 2, "Only one implies per statement in %s condition %s" % (ensurement, func.__name__)
                    e = "((%s) if (%s) else True) and ((%s) if (%s) else True)" % (e_parts[1], e_parts[0], e_parts[0], e_parts[1])
                    assert "-->" not in e, "Only one implies per statement in %s condition %s"  % (ensurement, func.__name__)
                if "-->" in e:
                    e_parts = e.split("-->")
                    assert len(e_parts) == 2, "Only one implies per statement in %s condition %s" % (ensurement, func.__name__)
                    e = "(%s) if (%s) else True" % (e_parts[1], e_parts[0])
                if "`" in e:
                    bt = "__BACKTICK__"
                    exec_cache = get_fun_prop(func, "exec_cache")
                    for cache_item in exec_cache:
                        limited_locals.update({k+bt : v for k,v in cache_item.items()})
                        e = e.replace("`", bt)
                        if not eval(e, globals(), limited_locals):
                            print("DEBUG INFORMATION:", limited_locals)
                            raise ExitConditionsError("Ensures statement '%s' failed in %s" % (ensurement, func.__name__))
                elif not eval(e, globals(), limited_locals):
                    print("DEBUG INFORMATION:", limited_locals)
                    raise ExitConditionsError("Ensures statement '%s' failed in %s" % (ensurement, func.__name__))
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
    theseargtypes = [TypeFactory(a) for a in argtypes]
    thesekwargtypes = {k : TypeFactory(a) for k,a in kwargtypes.items()}
    def _decorator(func):
        # @accepts decorator
        f = func.__wrapped__ if hasattr(func, "__wrapped__") else func
        try:
            argtypes = inspect.getcallargs(f, *theseargtypes, **thesekwargtypes)
            argtypes = {k: v if issubclass(type(v), Type) else Constant(v)
                        for k,v in argtypes.items()}
        except TypeError:
            raise ArgumentTypeError("Invalid argument specification to @accepts in %s" % func.__name__)
        if has_fun_prop(func, "argtypes"):
            raise ValueError("Cannot set argument types twice")
        set_fun_prop(func, "argtypes", argtypes)
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

def immutable_argument(func):
    set_fun_prop(func, "immutable_argument", True)
    return _wrap(func)


def verifiedclass(cls):
    for methname in dir(cls):
        meth = getattr(cls, methname)
        if has_fun_prop(meth, "argtypes"):
            argtypes = get_fun_prop(meth, "argtypes")
            if "self" in argtypes and isinstance(argtypes["self"], Self):
                argtypes["self"] = Generic(cls)
                set_fun_prop(meth, "argtypes", argtypes) # TODO Not necessary because of reference
    return cls
