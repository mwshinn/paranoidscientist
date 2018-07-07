# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

from .exceptions import InternalError
import inspect

_FUN_PROPS = "__verify__" # Name of dict used internally to store function properties

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
        raise InternalError("Invalid properties dictionary for %s" % str(f))
    getattr(f, _FUN_PROPS)[k] = v

def get_func_posargs_name(f):
    """Returns the name of the function f's keyword argument parameter if it exists, otherwise None"""
    sigparams = inspect.signature(f).parameters
    for p in sigparams:
        if sigparams[p].kind == inspect.Parameter.VAR_POSITIONAL:
            return sigparams[p].name
    return None

def get_func_kwargs_name(f):
    """Returns the name of the function f's keyword argument parameter if it exists, otherwise None"""
    sigparams = inspect.signature(f).parameters
    for p in sigparams:
        if sigparams[p].kind == inspect.Parameter.VAR_KEYWORD:
            return sigparams[p].name
    return None
