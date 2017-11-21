__all__ = ['accepts', 'requires', 'returns', 'ensures', 'immutable_argument', 'verifiedclass']
import functools
import inspect
from copy import deepcopy
from . import utils as U
from .types import base as T
from . import exceptions as E

RECURSIVE_LIMIT_WHILE_EXEC = 100 # TODO temporary hack to improve performance, will change later.

def _wrap(func):
    def _decorated(*args, **kwargs):
        # @accepts decorator
        if U.has_fun_prop(func, "argtypes"):
            argtypes = U.get_fun_prop(func, "argtypes")
            argvals = inspect.getcallargs(func, *args, **kwargs)
            if sorted(argtypes.keys()) != sorted(argvals.keys()):
                raise E.ArgumentTypeError("Invalid argument specification in %s" % func.__name__)
            for k in argtypes.keys():
                try:
                    argtypes[k].test(argvals[k])
                except AssertionError as e:
                    raise E.ArgumentTypeError("Invalid argument type: %s=%s is not of type %s in %s" % (k, argvals[k], argtypes[k], func.__name__))
        # @requires decorator
        if U.has_fun_prop(func, "requires"):
            argvals = inspect.getcallargs(func, *args, **kwargs)
            # Function named arguments
            #full_locals = locals().copy()
            #full_locals.update({k : v for k,v in zip(argspec.args, args)})
            full_locals = argvals
            for requirement in U.get_fun_prop(func, "requires"):
                if not eval(requirement, globals(), full_locals):
                    raise E.EntryConditionsError("Function requirement '%s' failed in %s" % (requirement,  func.__name__))
        # Function argument comparison: Allow testing for function
        # arguments which were modified.  To do so, first save an
        # extra copy of the testcase.
        if U.has_fun_prop(func, "immutable_argument"):
            prev_args = deepcopy(args)
            prev_kwargs = deepcopy(kwargs)
        # The actual function
        returnvalue = func(*args, **kwargs)
        # @returns decorator
        if U.has_fun_prop(func, "returntype"):
            try:
                U.get_fun_prop(func, "returntype").test(returnvalue)
            except AssertionError as e:
                raise E.ReturnTypeError("Invalid return type of %s in %s" % (returnvalue, func.__name__) )
        # Function argument comparison: To finish comparing arguments,
        # test the arguments for equality.  We cannot check for simple
        # equality because many objects have identity equality
        # built-in, so testing from a deepcopy is guaranteed to fail,
        # i.e. deepcopy(a) != a.  So, if the argument has a __dict__
        # property, we try comparing that.  Otherwise, we compare the
        # value.
        if U.has_fun_prop(func, "immutable_argument"):
            for a1,a2 in zip(prev_args,args):
                if not U.test_equality(a1, a2):
                    raise E.ObjectModifiedError
            for k in kwargs.keys():
                if not U.test_equality(prev_kwargs[k], kwargs[k]):
                    raise E.ObjectModifiedError
        # @ensures decorator
        if U.has_fun_prop(func, "ensures"):
            argtypes = U.get_fun_prop(func, "argtypes")
            argvals = inspect.getcallargs(func, *args, **kwargs)
            # Function named arguments
            limited_locals = argvals
            # Return value
            limited_locals['__RETURN__'] = returnvalue
            if any(hasbt for hasbt,_,_ in U.get_fun_prop(func, "ensures")) : # Cache if we refer to previous executions
                if U.has_fun_prop(func, "exec_cache"):
                    exec_cache = U.get_fun_prop(func, "exec_cache")
                else:
                    exec_cache = []
                    U.set_fun_prop(func, "exec_cache", exec_cache)
                exec_cache.append(limited_locals.copy())
                if len(exec_cache) > RECURSIVE_LIMIT_WHILE_EXEC:
                    exec_cache.pop(0) # TODO Hack for now, change this mechanism
            for hasbt, ensurement, etext in U.get_fun_prop(func, "ensures"):
                if hasbt:
                    bt = "__BACKTICK__"
                    exec_cache = U.get_fun_prop(func, "exec_cache")
                    for cache_item in exec_cache:
                        limited_locals.update({k+bt : v for k,v in cache_item.items()})
                        if not eval(ensurement, globals(), limited_locals):
                            print("DEBUG INFORMATION:", limited_locals)
                            raise E.ExitConditionsError("Ensures statement '%s' failed in %s" % (etext, func.__name__))
                else:
                    if not eval(ensurement, globals(), limited_locals):
                        print("DEBUG INFORMATION:", limited_locals)
                        raise E.ExitConditionsError("Ensures statement '%s' failed in %s" % (etext, func.__name__))
        return returnvalue
    if U.has_fun_prop(func, "active"):
        return func
    else:
        U.set_fun_prop(func, "active", True)
        assign = functools.WRAPPER_ASSIGNMENTS + (U._FUN_PROPS,)
        wrapped = functools.wraps(func, assigned=assign)(_decorated)
        if "__ALL_FUNCTIONS" in globals().keys():
            __ALL_FUNCTIONS.append(wrapped)
        return wrapped

def accepts(*argtypes, **kwargtypes):
    theseargtypes = [T.TypeFactory(a) for a in argtypes]
    thesekwargtypes = {k : T.TypeFactory(a) for k,a in kwargtypes.items()}
    def _decorator(func):
        # @accepts decorator
        f = func.__wrapped__ if hasattr(func, "__wrapped__") else func
        try:
            argtypes = inspect.getcallargs(f, *theseargtypes, **thesekwargtypes)
            argtypes = {k: v if issubclass(type(v), T.Type) else T.Constant(v)
                        for k,v in argtypes.items()}
        except TypeError:
            raise E.ArgumentTypeError("Invalid argument specification to @accepts in %s" % func.__name__)
        if U.has_fun_prop(func, "argtypes"):
            raise ValueError("Cannot set argument types twice")
        U.set_fun_prop(func, "argtypes", argtypes)
        return _wrap(func)
    return _decorator

def returns(returntype):
    returntype = T.TypeFactory(returntype)
    def _decorator(func):
        # @returns decorator
        if U.has_fun_prop(func, "returntype"):
            raise ValueError("Cannot set return type twice")
        U.set_fun_prop(func, "returntype", returntype)
        return _wrap(func)
    return _decorator

def requires(condition):
    def _decorator(func):
        # @requires decorator
        if U.has_fun_prop(func, "requires"):
            if not isinstance(U.get_fun_prop(func, "requires"), list):
                raise E.InternalError("Invalid requires structure")
            base_requires = U.get_fun_prop(func, "requires")
        else:
            base_requires = []
        U.set_fun_prop(func, "requires", [compile(condition, '', 'eval')]+base_requires)
        return _wrap(func)
    return _decorator

def ensures(condition):
    def _decorator(func):
    # @ensures decorator
        if U.has_fun_prop(func, "ensures"):
            if not isinstance(U.get_fun_prop(func, "ensures"), list):
                raise E.InternalError("Invalid ensures strucutre")
            ensures_statements = U.get_fun_prop(func, "ensures")
        else:
            ensures_statements = []
        e = condition.replace("return", "__RETURN__")
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
            e = e.replace("`", bt)
            compiled = compile(e, '', 'eval')
            U.set_fun_prop(func, "ensures", [(True, compiled, condition)]+ensures_statements)
        else:
            compiled = compile(e, '', 'eval')
            U.set_fun_prop(func, "ensures", [(False, compiled, condition)]+ensures_statements)
        return _wrap(func)
    return _decorator

def immutable_argument(func):
    U.set_fun_prop(func, "immutable_argument", True)
    return _wrap(func)


def verifiedclass(cls):
    for methname in dir(cls):
        meth = getattr(cls, methname)
        if U.has_fun_prop(meth, "argtypes"):
            argtypes = U.get_fun_prop(meth, "argtypes")
            if "self" in argtypes and isinstance(argtypes["self"], T.Self):
                argtypes["self"] = T.Generic(cls)
                U.set_fun_prop(meth, "argtypes", argtypes) # TODO Not necessary because of reference
    return cls
