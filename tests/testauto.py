from paranoid import *
from paranoid.testfunctions import test_function

def fails(f):
    failed = False
    try:
        f()
    except:
        failed = True
    if failed == False:
        raise ValueError("Error, function did not fail")

# Tests
@accepts(Number())
#@returns(Number())
def add_three(n):
    return n+3

add_three(4)
add_three(-10)
fails(lambda : add_three("hello"))

@accepts(Number(), Number())
@returns(Number())
def add(n, m):
    return n+m

add(4, 5)

@accepts(Number(), Number())
@requires("n >= m")
@returns(Number())
@ensures("return >= 0")
def subtract(n, m):
    return n - m

@accepts(Range(-1, 1))
@returns(Range(0, 1))
def square(n):
    return n*n

square(.3)

@accepts(RangeClosedOpen(-1, 1))
@returns(Range(0, 1))
def square(n):
    return n*n

square(-1)
fails(lambda : square(1))

@accepts(RangeOpenClosed(-1, 1))
@returns(Range(0, 1))
def square(n):
    return n*n

square(1)
fails(lambda : square(-1))

@accepts(RangeOpen(-1, 1))
@returns(RangeClosedOpen(0, 1))
def square(n):
    return n*n

square(.99999)
fails(lambda : square(1))

@accepts(List(Integer()))
@returns(Integer())
def sumlist(l):
    return sum(l)

sumlist([3, 6, 2, 1])

@accepts(Dict(String(), Number()))
@returns(Dict(String(), Number()))
def ident(d):
    return d

ident({"a" : 3, "b" : 901.90})
fails(lambda : ident({"a" : "a", "b" : 901.90, "c" : 22}))
fails(lambda : ident({"a" : 33, "b" : 901.90, 22 : 22}))

class MyType:
    def __init__(self, val):
        self.val = val
    @staticmethod
    def _generate():
        vals = ["string", 3, 11]
        return [MyType(v) for v in vals]

@accepts(MyType)
@returns(MyType)
def myfun(mt):
    return MyType(3)

myfun(MyType(1))
fails(lambda : myfun("abc"))

@accepts(And(Natural0(), Or(Range(low=4, high=7), Range(low=12, high=15))))
@returns(Natural1())
def addthree(a):
    return a+3

addthree(4)
addthree(5)
fails(lambda : addthree(9))
fails(lambda : addthree(2))

@accepts(String)
@returns(Nothing)
def pass_it(s):
    pass

pass_it("ars")

@accepts(Number())
@returns(Number())
@ensures("n` <= n <--> return` <= return")
def monotonic(n):
    return n**3

monotonic(-3)
monotonic(-2)
monotonic(-1)

test_function(monotonic)

@accepts(Number(), Number())
@returns(Number())
@ensures("return == n + m")
@ensures("return >= m + n")
@ensures("m > 0 and n > 0 --> return > 0")
@ensures("m` >= m and n` >= n --> return` >= return")
def add(n, m):
    return n+m

add(0, 5)
add(0, 6)
add(0, 3)
add(7, 3)

test_function(add)

@paranoidclass
class MyClass:
    def __init__(self, val, **kwargs):
        self.val = val
        self.extraargs = kwargs
    @staticmethod
    def _test(v):
        Number().test(v.val)
        Dict(String(), String()).test(v.extraargs)
    @staticmethod
    def _generate():
        vals = [3, 11, -3.1]
        return [MyClass(v, extraarg='ata') for v in vals]
    @accepts(Self, Number)
    def testfun(self, x):
        return self.val + x
    @accepts(Self, Number)
    @returns(Number)
    def testfun2(self, x, **kwargs):
        return self.val + x

