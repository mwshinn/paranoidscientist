# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

class VerifyError(Exception):
    """Base class for Paranoid Scientist exceptions"""
    pass


class ArgumentTypeError(VerifyError):
    """A function was passed an argument of the wrong type."""
    pass

class EntryConditionsError(VerifyError):
    """A function's entry conditions were not satisfied."""
    pass

class ReturnTypeError(VerifyError):
    """A function returned a value of the wrong type."""
    pass

class ExitConditionsError(VerifyError):
    """A function's exit conditions were not satisfied."""
    pass


class InvalidTypeError(VerifyError):
    """A type was not implemented correctly."""
    pass

class NoGeneratorError(VerifyError):
    """A type does not have a valid generate() function."""
    pass

class InternalError(VerifyError):
    """This should not happen."""
    pass

class ObjectModifiedError(VerifyError):
    """A static object was modified."""
    pass


class TestCaseTimeoutError(VerifyError):
    """Thrown to allow function timeouts."""
    pass
