# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

"""Function (and class) decorators which constitute the primary Paranoid Scientist interface"""

__all__ = ['accepts', 'requires', 'returns', 'ensures', 'paranoidclass', 'paranoidconfig']
import functools, itertools
import inspect
from random import randint
from copy import deepcopy
from . import utils as U
from .types import base as T
from .types.collections import Dict, List
from .types.string import String
from . import exceptions as E
from .settings import Settings

# Constants used internally
_BT = "__BACKTICK__"
_RET = "__RETURN__"


def _check_accepts(func, argvals):
    # @accepts decorator
    if U.has_fun_prop(func, "argtypes"):
        argtypes = U.get_fun_prop(func, "argtypes")
        if sorted(argtypes.keys()) != sorted(argvals.keys()):
            raise E.ArgumentTypeError("Invalid argument specification in %s" % func.__name__)
        for k in argtypes.keys():
            try:
                argtypes[k].test(argvals[k])
            except AssertionError as e:
                raise E.ArgumentTypeError("Invalid argument type: %s=%s is not of type %s in %s" % (k, argvals[k], argtypes[k], func.__qualname__))

def _check_requires(func, argvals):
    # @requires decorator
    if U.has_fun_prop(func, "requires"):
        # Function named arguments
        full_globals = Settings.get("namespace").copy()
        full_globals.update(argvals)
        #full_locals = locals().copy()
        #full_locals.update({k : v for k,v in zip(argspec.args, args)})
        for requirement,requirementtext in U.get_fun_prop(func, "requires"):
            try:
                if not eval(requirement, full_globals, {}):
                    raise E.EntryConditionsError("Function requirement '%s' failed in %s\nparams: %s" % (requirementtext,  func.__qualname__, str(argvals)))
            except Exception as e:
                if isinstance(e, E.EntryConditionsError):
                    raise
                else:
                    raise E.EntryConditionsError("Invalid function requirement '%s' in %s\nparams: %s" % (requirementtext,  func.__qualname__, str(argvals)))

def _check_returns(func, returnvalue):
    # @returns decorator
    if U.has_fun_prop(func, "returntype"):
        try:
            U.get_fun_prop(func, "returntype").test(returnvalue)
        except AssertionError as e:
            raise E.ReturnTypeError("Invalid return type of %s in %s" % (returnvalue, func.__qualname__) )

def _check_ensures(func, returnvalue, argvals):
    # @ensures decorator
    if U.has_fun_prop(func, "ensures"):
        # This function call
        current_call = argvals
        current_call[_RET] = returnvalue
        if U.has_fun_prop(func, "exec_cache"):
            exec_cache = U.get_fun_prop(func, "exec_cache")
        else:
            exec_cache = []
        for btdepth, ensurement, etext in U.get_fun_prop(func, "ensures"):
            # Here we check the higher order properties, e.g. x,
            # x`, and x``. There is a lot of repeated and opaque
            # code here, but I've tried to write it in the
            # cleanest way possible.
            for comb in itertools.combinations(exec_cache, btdepth):
                for params in itertools.permutations([current_call]+list(comb)):
                    env = dict()
                    for i in range(0, btdepth+1):
                        bts = "".join([_BT for j in range(0, i)])
                        env.update({k+bts : v for k,v in params[i].items()})
                    limited_globals = Settings.get("namespace").copy()
                    limited_globals.update(env)
                    if not eval(ensurement, limited_globals, {}):
                        env_simp = {k.replace(_BT, '`').replace(_RET, 'return'): v for k,v in env.items()}
                        raise E.ExitConditionsError("Ensures statement '%s' failed in %s\nparams: %s" % (etext, func.__qualname__, str(env_simp)))
        # Update the cache
        if any(btdepth>0 for btdepth,_,_ in U.get_fun_prop(func, "ensures")) : # Cache if we refer to previous executions
            # Keep track of number of executions for reservoir
            # sampling probabilities
            if exec_cache == []:
                n_execs = 1
                U.set_fun_prop(func, "exec_cache", exec_cache) # Create exec cache if it doesn't exist
            else:
                n_execs = U.get_fun_prop(func, "n_execs") + 1
            U.set_fun_prop(func, "n_execs", n_execs)
            # Use reservoir sampling to maintain the cache
            max_cache_size = Settings.get("max_cache", function=func)
            if n_execs <= max_cache_size:
                exec_cache.append(current_call)
            else:
                rn = randint(0, n_execs)
                if rn < max_cache_size:
                    exec_cache[rn] = current_call


def _wrap(func):
    def _decorated(*args, **kwargs):
        # Skip verification if paranoid is disabled.
        if Settings.get("enabled", function=func) == False:
            return func(*args, **kwargs)
        # We only run this function once for performance reasons, and
        # then pass it as an argument to each check function.
        sig = inspect.Signature.from_callable(func)
        boundargs = sig.bind_partial(*args, **kwargs)
        boundargs.apply_defaults()
        argvals = dict(boundargs.arguments)

        # Check entry conditions, run the function, check exit
        # conditions, and return the result of the function.
        _check_accepts(func, argvals)
        _check_requires(func, argvals)
        returnvalue = func(*args, **kwargs)
        _check_returns(func, returnvalue)
        _check_ensures(func, returnvalue, argvals)
        return returnvalue
    
    if U.has_fun_prop(func, "active"):
        return func
    else:
        U.set_fun_prop(func, "active", True)
        assign = functools.WRAPPER_ASSIGNMENTS + \
                 (U._FUN_PROPS, Settings.FUNCTION_SETTINGS_NAME)
        wrapped = functools.wraps(func, assigned=assign)(_decorated)
        # A list of all functions for when Paranoid Scientist is
        # invoked with "python3 -m paranoid scriptname.py".  If the
        # name "__ALL_FUNCTIONS" is not defined, then we assume
        # paranoid was not called in this way.  If it is defined, we
        # add this function to the list.
        if "__ALL_FUNCTIONS" in globals().keys():
            __ALL_FUNCTIONS.append(wrapped)
        return wrapped

def accepts(*argtypes, **kwargtypes):
    """A function decorator to specify argument types of the function.

    Types may be specified either in the order that they appear in the
    function or via keyword arguments (just as if you were calling the
    function).

    Example usage:

      | @accepts(Positive0)
      | def square_root(x):
      |     ...
    """

    theseargtypes = [T.TypeFactory(a) for a in argtypes]
    thesekwargtypes = {k : T.TypeFactory(a) for k,a in kwargtypes.items()}
    def _decorator(func):
        # @accepts decorator
        f = func.__wrapped__ if hasattr(func, "__wrapped__") else func
        sig = inspect.signature(f)
        boundargs = sig.bind(*theseargtypes, **thesekwargtypes)
        argtypes = {}
        # Loop through each of the parameters in the function's call
        # signature and make sure they were passed to @accepts
        for p in sig.parameters.values():
            # Keyword arguments get the KeywordArguments() type.
            if p.kind == p.VAR_KEYWORD:
                if p.name in boundargs.arguments.keys():
                    raise E.ArgumentTypeError("Unexpected keyword arguments to @accepts in %s" % f.__qualname__)
                argtypes[p.name] = T.KeywordArguments()
            # Positional arguments get the PositionalArguments() type.
            elif p.kind == p.VAR_POSITIONAL:
                if p.name in boundargs.arguments.keys():
                    raise E.ArgumentTypeError("Unexpected arguments to @accepts in %s" % f.__qualname__)
                argtypes[p.name] = T.PositionalArguments()
            # Handle all normal arguments
            else:
                if p.name not in boundargs.arguments.keys():
                    raise E.ArgumentTypeError("Invalid argument specification to @accepts in %s" % f.__qualname__)
                argtypes[p.name] = T.TypeFactory(boundargs.arguments[p.name])
        # Make sure extra arguments weren't passed to @accepts
        if set(boundargs.arguments.keys()) - set(sig.parameters.keys()) != set():
            raise E.ArgumentTypeError("Invalid argument specification to @accepts in %s" % f.__qualname__)
        # Make sure @accepts hasn't already been called on this function
        if U.has_fun_prop(func, "argtypes"):
            raise ValueError("Cannot set argument types twice")
        U.set_fun_prop(func, "argtypes", argtypes)
        return _wrap(func)
    return _decorator

def returns(returntype):
    """A function decorator to specify return type of the function.

    Example usage:

      | @accepts(Positive0)
      | @returns(Positive0)
      | def square_root(x):
      |     ...
    """
    returntype = T.TypeFactory(returntype)
    def _decorator(func):
        # @returns decorator
        if U.has_fun_prop(func, "returntype"):
            raise ValueError("Cannot set return type twice")
        U.set_fun_prop(func, "returntype", returntype)
        return _wrap(func)
    return _decorator

# Adds the "requires" property: list of (compiledcondition, conditiontext)
def requires(condition):
    """A function decorator to specify entry conditions for the function.

    Entry conditions should be a string, which will be evaluated as
    Python code.  Arguments of the function may be accessed by their
    name.

    The special syntax "-->" and "<-->" may be used to mean "if" and
    "if and only if", respectively.  They may not be contained within
    sub-expressions.

    Note that globals will not be included by default, and must be
    manually included using the "namespace" setting, set via
    settings.Settings.

    Example usage:

      | @requires("x >= y")
      | def subtract(x, y):
      |     ...

      | @accepts(l=List(Number), log_transform=Boolean)
      | @requires("log_transform == True --> min(l) > 0")
      | def process_list(l, log_transform=False):
      |     ...
    """
    def _decorator(func, condition=condition):
        # @requires decorator
        if U.has_fun_prop(func, "requires"):
            if not isinstance(U.get_fun_prop(func, "requires"), list):
                raise E.InternalError("Invalid requires structure")
            base_requires = U.get_fun_prop(func, "requires")
        else:
            base_requires = []
        base_condition = condition
        if "<-->" in condition:
            condition_parts = condition.split("<-->")
            assert len(condition_parts) == 2, "Only one implies per statement in %s condition %s" % (condition, func.__qualname__)
            condition = "((%s) if (%s) else True) and ((%s) if (%s) else True)" % (condition_parts[1], condition_parts[0], condition_parts[0], condition_parts[1])
        elif "-->" in condition:
            condition_parts = condition.split("-->")
            assert len(condition_parts) == 2, "Only one implies per statement in %s condition %s" % (base_condition, func.__qualname__)
            condition = "(%s) if (%s) else True" % (condition_parts[1], condition_parts[0])

        U.set_fun_prop(func, "requires", [(compile(condition, '', 'eval'), condition)]+base_requires)
        return _wrap(func)
    return _decorator

# Adds the "requires" property: list of (backtickdepth, compiledcondition, conditiontext)
def ensures(condition):
    """A function decorator to specify exit conditions for the function.

    Exit conditions should be a string, which will be evaluated as
    Python code.  Arguments of the function may be accessed by their
    name.  The return value of the function may be accessed using the
    special variable name "return".

    The special syntax "-->" and "<-->" may be used to mean "if" and
    "if and only if", respectively.  They may not be contained within
    sub-expressions.

    Values may be compared to previous executions of the function by
    including a "`" or "``" after them to check for higher order
    properties of the function.

    Note that globals will not be included by default, and must be
    manually included using the "namespace" setting, set via
    settings.Settings.

    Example usage:

      | @ensures("lower_bound <= return <= upper_bound")
      | def search(lower_bound, upper_bound):
      |     ...

      | @ensures("x <= x` --> return <= return`")
      | def monotonic(x):
      |     ...
    """
    def _decorator(func, condition=condition):
    # @ensures decorator
        if U.has_fun_prop(func, "ensures"):
            if not isinstance(U.get_fun_prop(func, "ensures"), list):
                raise E.InternalError("Invalid ensures strucutre")
            ensures_statements = U.get_fun_prop(func, "ensures")
        else:
            ensures_statements = []
        e = condition.replace("return", _RET)
        if "<-->" in e:
            e_parts = e.split("<-->")
            assert len(e_parts) == 2, "Only one implies per statement in %s condition %s" % (ensurement, func.__qualname__)
            e = "((%s) if (%s) else True) and ((%s) if (%s) else True)" % (e_parts[1], e_parts[0], e_parts[0], e_parts[1])
            assert "-->" not in e, "Only one implies per statement in %s condition %s"  % (ensurement, func.__qualname__)
        if "-->" in e:
            e_parts = e.split("-->")
            assert len(e_parts) == 2, "Only one implies per statement in %s condition %s" % (ensurement, func.__qualname__)
            e = "(%s) if (%s) else True" % (e_parts[1], e_parts[0])
        # btdepth is the maximum number of consecutive ` characters
        # that appears in the ensures statement, and represents power
        # of the number of comparisons we must perform on cached
        # values.
        btdepth = max([0]+[sum(1 for x in g) for c,g in itertools.groupby(e) if c == "`"])
        e = e.replace("`", _BT)
        compiled = compile(e, '', 'eval')
        U.set_fun_prop(func, "ensures", [(btdepth, compiled, condition)]+ensures_statements)
        return _wrap(func)
    return _decorator


def paranoidclass(cls):
    """A class decorator to specify that class methods contain paranoid decorators.

    Example usage:

      | @paranoidclass
      | class Point:
      |     def __init__(self, x, y):
      |         ...
      |     @returns(Number)
      |     def distance_from_zero():
      |         ...
    """
    for methname in dir(cls):
        meth = getattr(cls, methname)
        if U.has_fun_prop(meth, "argtypes"):
            argtypes = U.get_fun_prop(meth, "argtypes")
            for argname in argtypes.keys():
                if isinstance(argtypes[argname], T.Self):
                    # "self" means something different in the __init__
                    # method than it does in other methods
                    if methname == "__init__" and argname == "self":
                        argtypes[argname] = T.InitGeneric(cls)
                    else:
                        argtypes[argname] = T.Generic(cls)
                # Somewhat of a hack to get And/Or to work with Self
                if isinstance(argtypes[argname], T.Or) or isinstance(argtypes[argname], T.And):
                    for i in range(0, len(argtypes[argname].types)):
                        if isinstance(argtypes[argname].types[i], T.Self):
                            argtypes[argname].types[i] = T.Generic(cls)
        if U.has_fun_prop(meth, "returntype"):
            if isinstance(U.get_fun_prop(meth, "returntype"), T.Self):
                U.set_fun_prop(meth, "returntype", T.Generic(cls))
    return cls

def paranoidconfig(**kwargs):
    """A function decorator to set a local setting.

    Settings may be set either globally (using
    settings.Settings.set()) or locally using this decorator.  The
    setting name should be passed as a keyword argument, and the value
    to assign the setting should be passed as the value.  See
    settings.Settings for the different settings which can be set.

    Example usage:
    
      | @returns(Number)
      | @paranoidconfig(enabled=False)
      | def slow_function():
      |     ...
    """
    def _decorator(func):
        for k,v in kwargs.items():
            Settings._set(k, v, function=func)
        return _wrap(func)
    return _decorator
