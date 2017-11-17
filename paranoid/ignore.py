def accepts(*argtypes, **kwargtypes):
    return lambda f: f

def returns(returntype):
    return lambda f: f
            
def requires(condition):
    return lambda f: f

def ensures(condition):
    return lambda f: f

def immutable_argument(func):
    return func

def verifiedclass(cls):
    return cls
