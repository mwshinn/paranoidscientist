from verify import *

# Tests
@accepts(Number())
@returns(Number())
def add_three(n):
    return n+3

add_three(4)
add_three(-10)
#add_three("hello")

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
#square(.999)

@accepts(RangeClosedOpen(-1, 1))
@returns(Range(0, 1))
def square(n):
    return n*n

square(-1)
#square(1)

@accepts(RangeOpenClosed(-1, 1))
@returns(Range(0, 1))
def square(n):
    return n*n

square(1)
#square(-1)

@accepts(RangeOpen(-1, 1))
@returns(RangeOpen(0, 1))
def square(n):
    return n*n

square(.99999)
#square(1)

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
#ident({"a" : "a", "b" : 901.90, "c" : 22})
#ident({"a" : 33, "b" : 901.90, 22 : 22})

class MyType:
    def __init__(self, val):
        self.val = val

@accepts(MyType)
@returns(MyType)
def myfun(mt):
    return MyType(3)

myfun(MyType(1))
#myfun("abc")

@accepts(And(Natural0(), Range(low=4, high=7)))
@returns(Natural1())
def addthree(a):
    return a+3

addthree(4)
addthree(5)
#addthree(9)
#addthree(2)
