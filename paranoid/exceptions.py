# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

class VerifyError(Exception):
    pass


class ArgumentTypeError(VerifyError):
    pass

class EntryConditionsError(VerifyError):
    pass

class ReturnTypeError(VerifyError):
    pass

class ExitConditionsError(VerifyError):
    pass


class InvalidTypeError(VerifyError):
    pass

class NoGeneratorError(VerifyError):
    pass

class InternalError(VerifyError):
    pass

class ObjectModifiedError(VerifyError):
    pass


class TestCaseTimeoutError(VerifyError):
    pass
