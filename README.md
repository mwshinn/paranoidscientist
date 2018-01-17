Paranoid Scientist
==================

## What is Paranoid Scientist?

Paranoid Scientist is a Python module which provides allows runtime
verification for Python programs.  More specifically, it provides the
following:

- A strong type system, which emphasizes the *meaning* of the type
  instead of the *data structure* of the type.
- Verification of arbitrary entry and exit conditions, including more
  complex expressions with universal quantification.
- Automated testing of individual functions to determine, before
  execution of the program, whether functions conform to their
  specification.
- A simple and clear function decorator notation

It shares inspiration (but is still quite distinct) from
contract-based programming, type classes, and automated fuzz testing,

## What is the point?

Paraoid Scientist is a tool to make sure scientific code is correct.
Traditional program verification asks the question, "If I run my code,
will it run correctly?"  It can be used to verify, for instance, that
a compiler will always produce the expected output.  In practice, it
can take a lot of time to verify programs and requires the use of
specific programming languages and constructs.

In scientific programming, verification is especially important
because we do not know the expected results of a computation, so it is
difficult to know whether any results are due to software bugs.  Thus,
with a slightly different goal, we can relax the question above and
instead ask, "If I ran my code, did it run correctly?"  In other
words, it is not as important to know before executing the program
whether it will run correctly, but if the program gives a result, we
want to know that this result is correct.

## Is Paranoid Scientist "Pythonic"?

Paranoid Scientist is Pythonic in most aspects, but not at all in the
type system.  Pythonic code relies on duck typing, which is great in
many situations but is a nightmare for scientific programming.  As an
example, consider the following:

```python
M = get_data_as_matrix()
M_squared = M**2
print(M_squared.tolist())
```

What is the result of this computation?  Duck typing tells us that we
have squared the matrix, and thus everything is okay.  However, if we
look more closely, the result depends on the matrix type returned by
`get_data_as_matrix`:

```python
M = numpy.matrix([[1, 2], [3, 4]])
M_squared = M**2
print(M_squared.tolist())

M = numpy.array([[1, 2], [3, 4]])
M_squared = M**2
print(M_squared.tolist())
```

which outputs

```
[[7, 10], [15, 22]]
[[1, 4], [9, 16]]
```

As we can see, the result of this computation depends on whether the
matrix is a numpy array or a numpy matrix, both of which are common
datatypes in practice.  The former implement element-wise
multiplication, while the latter implements matrix multiplication.
Forgetting to cast an array to a matrix (or vice versa) can introduce
subtle bugs into your code that could easily go undetected.

## System requirements

- Python 3.6 or above
- Optional: Numpy (for Numpy types support)

## Introduction to Types

The term "type" in Paranoid Scientist does not mean "type" in the same
sense that a programming language might use the word.  "Types" here do
not depend on the internal respresentation of variables, but rather,
on the way that they will be interpreted by humans.

As an example, suppose we want to implement a function which takes a
decimal number.  In a static-typed language, which uses
compiler/interpreter datatypes, this function would take a float as a
parameter.  However, it is not clear whether the function's behavior
is defined for NaN or Inf values.  While these are valid floats, they
are not valid decimal numbers.  Additionally, in a statically types
language, even though the function may also be valid for integers, the
code will require function polymorphism.  Thus, there is a disconnect
between what it means for a variable to be a "number"; a single
datatype is neither necessary nor sufficient to capture this concept.

By contrast, Paranoid Scientist considers "types" to be those which
are most useful in helping humans to reason about code.  For instance,
consider the following function:

```python
def add(n, m):
    """Compute n + m"""
    return n+m
```

This function works for any number, whether it is an integer or a
floating point, but it doesn't work for NaN or Inf.  So, we can
annotate the function as follows:

```python
@accepts(Number, Number)
@returns(Number)
def add(n, m):
    """Compute n + m"""
    return n+m
```

The "Number" type includes both floating points and integers, but
excludes NaN and Inf.

Similarly, we can use other human-undestandable types.  The following
function computes the expected number of "heads" in a biased coin,
when we flip a coin with a `p_heads` probability of showing heads
`flips` number of times.

```python
@accepts(Natural1, Range(0, 1))
@returns(Natural0)
def biased_coin(flips, p_heads):
    return round(flips * p_heads)
```

The `Natural1` type represents a natural number excluding zero, the
`Natural0` type is a natural number including zero, and `Range` is any
number within the range.

## Creating custom types

It is relatively easy to create new types, and expected that you will
need to make several new types for each script you use with Paranoid
Scientist.

There are two ways to make new types.  They can either be created from
scratch, or an existing class can be converted into a type.

### From scratch

A type is a class which can be used to evaluate whether an arbitrary
value is a part of the type, and to generate new values of the type. 

The simplest types consist of two main components: 

- A function called `test` to test values to see if they are a part of
  the type.  This function should accept one argument (the value to be
  tested), and should use **assert statements only** to test whether
  the value is of the correct type.  The function should have only two
  behaviors: executing successfully retuning nothing (if the value is
  of the correct type), or throwing an assertion error (if the value
  is not of the correct type).
- A generator called `generate` to create test cases for the type.  It
  should use Python's yield statement for each test case.  It should
  not throw any errors.

All types should inherit from `paranoid.base.Type`.

Consider the following simple type:

```
from paranoid.types.base import Type

class BinaryString(Type):
    """A binary number in the form of a string"""
    def test(self, v):
        """Test is `v` is a string of 0's and 1's."""
        # Use assert statements to verify the type
        assert set(v).difference({'0', '1'}) == set()
    def generate(self):
        """Generate some edge case binary strings"""
        yield "" # Empty list
        yield "0" # Just 0
        yield "1" # Just 1
        yield "01"*1000 # Long list
```

This works as expected

    >>> BinaryString().test("001")
    >>> "110101" in BinaryString()
    True
    >>> "012" in BinaryString()
    False
    >>> all([v in BinaryString() for v in BinaryString().generate()])
    True

Notice that in the constructor, we use the `in` syntax.  The syntax `x
in Natural0()` returns True if `Natural0().test(x)` does not raise an
exception.

A type may also contain arguments, in which case a constructor must
also be defined.  For instance, let's create a type for a binary
string of some particular length.  Since these must by definition also
be binary strings, we can inherit from the BinaryString type.

```
from paranoid.types.numeric import Natural0

class FixedLengthBinaryString(BinaryString):
    """A binary number of specified length in the form of a string."""
    def __init__(self, length):
        super().__init__()
        assert length in Natural0() # Length must be a natural number
        self.length = length
    def test(self, v):
        """Test if `v` is a binary string of length `length`."""
        super().test(v) # Make sure it is a binary string
        assert len(v) == self.length # Make sure it is the right length
    def generate(self):
        """Generate binary strings of length `length`."""
        yield "0"*self.length # All 0's
        yield "1"*self.length # All 1's
        if self.length % 2 == 0:
            yield "01"*(self.length//2)
        else:
            yield "01"*(self.length//2) + "0"
```

Again, this works as we expect it to.

    >>> FixedLengthBinaryString(4).test("0010")
    >>> "001" in FixedLengthBinaryString(3)
    True
    >>> "001" in FixedLengthBinaryString(4)
    False
    >>> all([v in FixedLengthBinaryString(4) \
             for v in FixedLengthBinaryString(4).generate()])
    True

### From an existing class

To come...

## Entry and exit conditions

To come...

## Automated testing

To come...

## License

All code is available under the GPLv3.

## FAQs

### Why are Python lists and numpy 1D arrays different types?

These types behave differently in many common situation which can lead
to bugs.  For instance, consider the following function:

```
def add_lists(a, b):
    return a + b
```

Does this concatenate the lists or does it perform element-wise
addition?  The answer depends on the datatype passed.

### Why are Numpy numbers different types than Python numbers?

As you may know, integers and floats in Python are different from
integers and floats in Numpy.  While both behave similarly in most
circumstances, Paranoid Scientist treats these as different types.

First, Numpy claims that their numeric type system is fully compatible
with Python's, however there are subtle differences, such as a failure
to pickle in some circumstances.

Second, and more importantly, incorporating Numpy features into a core
module for Paranoid Scientist would introduce an unnecessary
dependency on Numpy.
