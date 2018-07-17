# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

"""Automatic testing of a single function."""

import inspect
import itertools
import signal
from contextlib import contextmanager
from . import utils
from .exceptions import NoGeneratorError, EntryConditionsError, TestCaseTimeoutError
from .settings import Settings

@contextmanager
def max_run_time(t):
    """Limit the runtime of a code segment.

    If a block of code runs for more than `t` seconds, kill it.  This
    only works on unix platforms; on Windows, there will be no time
    limit.
    
    Use within a with statement, e.g.

        with max_run_time(5):
            potentially_long_function()
    """
    def callback(s=None, f=None):
        raise TestCaseTimeoutError
    if "alarm" in signal.__dict__ and "SIGALRM" in signal.__dict__:
        signal.signal(signal.SIGALRM, callback)
        signal.setitimer(signal.ITIMER_REAL, t)
        try:
            yield
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0) # Cancel alarm
    else:
        yield

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

    Returns the number of tests performed.
    """
    # Ensure the user has specified argument types using the @accepts
    # decorator.
    assert utils.has_fun_prop(func, "argtypes"), "No argument annotations"
    # Generate all combinations of arguments as test cases.  Some
    # argument types cannot be generated automatically.  If we
    # encounter one of these, unit testing won't work.
    args = utils.get_fun_prop(func, "argtypes")

    try:
        testcases = itertools.product(*[list(args[k].generate()) for k in sorted(args.keys())])
    except NoGeneratorError:
        testcases = []
    if not testcases:
        print("Warning: %s could not be tested" % func.__name__)
        return 0
    # If entry conditions are met, simply running the function will be
    # enough of a test, since all values are checked at runtime.  So
    # execute the function once for each combination of arguments.
    totaltests = 0
    for tc in testcases:
        kwargs_name = utils.get_func_kwargs_name(func)
        try:
            kws = tc[sorted(args.keys()).index(kwargs_name)] if kwargs_name else {}
            with max_run_time(Settings.get("max_runtime", function=func)):
                func(**{k : v for k,v in zip(sorted(args.keys()),tc) if k != kwargs_name},
                     **kws)
                totaltests += 1
        except EntryConditionsError:
            continue
        except TestCaseTimeoutError:
            print("Funciton timeout, continuing")
    return totaltests
