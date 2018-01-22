# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

from .exceptions import InternalError
import inspect

_FUN_PROPS = "__verify__"

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

# TODO this will fail for cyclical objects
def test_equality(a1, a2):
    if not hasattr(a1, "__dict__"):
        return a1 == a2
    if a1.__dict__ != a2.__dict__:
        if sorted(a1.__dict__.keys()) != sorted(a2.__dict__.keys()):
            return False
        for k in a1.__dict__.keys():
            if not test_equality(a1.__dict__[k], a2.__dict__[k]):
                return False
    return True
    

def get_func_kwargs_name(f):
    """Returns the name of the function f's keyword argument parameter if it exists, otherwise None"""
    sigparams = inspect.signature(f).parameters
    sig_kwargs = None
    for p in sigparams:
        if sigparams[p].kind == inspect.Parameter.VAR_KEYWORD:
            return sigparams[p].name
    return None
