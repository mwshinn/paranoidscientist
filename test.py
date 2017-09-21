from verify import *

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
@returns(Number())
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

@accepts(Range(-1, 1))
@returns(Range(0, .9))
def square(n):
    return n*n

square(.3)
fails(lambda : square(.999))

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
@returns(RangeOpen(0, 1))
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

@accepts(MyType)
@returns(MyType)
def myfun(mt):
    return MyType(3)

myfun(MyType(1))
fails(lambda : myfun("abc"))

@accepts(And(Natural0(), Range(low=4, high=7)))
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

@accepts(String)
@returns(Nothing)
def dont_pass_it(s):
    return False

fails(lambda : dont_pass_it("ars"))
