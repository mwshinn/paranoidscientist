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
