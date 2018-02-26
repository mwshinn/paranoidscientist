Paranoid Scientist
==================

## What is Paranoid Scientist?

Paranoid Scientist is a Python module which allows runtime
verification of entry and exit conditions for Python functions.  More
specifically, it provides the following:

- A strong type system, which emphasizes the *meaning* of the type
  instead of the *data structure* of the type.
- Verification of arbitrary entry and exit conditions, including more
  complex expressions with universal quantification.
- Automated testing of individual functions to determine, before
  execution of the program, whether functions conform to their
  specification.
- A simple and clear function decorator notation

It shares inspiration (but is still quite distinct) from
contract-based programming, type classes, and automated fuzz testing.

## Quick example

Paranoid Scientist is used to programmatically define and verify
function entry and exit conditions.  Here are some simple examples.

```python
from paranoid.types import Number, Positive, Natural1, Natural0, Range
from paranoid.decorators import accepts, returns, requires, ensures, paranoidclass

@accepts(x=Number, y=Number)
@returns(Positive)
@requires("x != y")
def some_formula(x, y):
    return 1/((x-y)**2)

@accepts(Number)
@returns(Number)
@ensures("x >= x` --> return >= return`") # Test for monotonicity
def cube(x):
    return x**3

# `flips` must be a natural number, but not 0
# `p_heads` must be between 0 and 1 inclusive
@accepts(Natural1, Range(0, 1))
# Returns a natural number, which may be 0
@returns(Natural0)
# We can never have more heads than flips
@ensures("return <= flips")
# If we have a zero probability, we get zero heads
@ensures("p_heads == 0 --> return == 0")
def biased_coin(flips, p_heads=0.5):
    """Expected number of heads from biased coin flips.
    
    `flips` should be the number of times to flip the coin.
    `p_heads` should be the probability of getting heads on one flip.
    """
    return round(flips * p_heads)
```

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

## System requirements

- Python 3.5 or above
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
from paranoid.decorators import accepts, returns
from paranoid.types import Number

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
from paranoid.decorators import accepts, returns
from paranoid.types import Natural1, Natural0, Range

@accepts(Natural1, Range(0, 1))
@returns(Natural0)
def biased_coin(flips, p_heads):
    return round(flips * p_heads)
```

The `Natural1` type represents a natural number excluding zero, the
`Natural0` type is a natural number including zero, and `Range` is any
number within the range.

Additionally, the same syntax can be used in class methods, as long as
the class is flagged with the `@paranoidclass` decorator.  The special
type `Self` should be used for the `self` arguments in class methods.

``` python
from paranoid.decorators import accepts, returns, paranoidclass
from paranoid.types import Self, Number, Boolean

@paranoidclass
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    @accepts(Self, Number, Number, Number, Number)
    @returns(Boolean)
    def is_in_box(self, xmin, xmax, ymin, ymax):
        if self.x > xmin and \
           self.x < xmax and \
           self.y > ymin and \
           self.y < ymax:
            return True
        return False
```

Currently, Paranoid Scientist does not operate on the `__init__`
method.  This is because, unlike all other methods in a class, the
`self` argument does not represent a fully instantiated class.  In
other words, the purpose of the `__init__` function is to help create
the `self` object, and therefore it does not make sense to test
whether the `self` object is valid, because clearly it is not.

## Creating types

It is relatively easy to create new types, and expected that you will
need to make several new types for each script you use with Paranoid
Scientist.

There are two ways to make new types.  They can either be created from
scratch, or an existing class can be converted into a type.

### Creating types from scratch

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

```python
from paranoid.types import Type

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

```python
from paranoid.types import Natural0

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

### Creating types from an existing class

Any normal Python class can be converted into a type.  In essence,
this allows the data within the class to be validated and tested.  Any
class can be turned into a type by adding two static methods:
`_test(v)`, and `_generate()`, which are analogous to the `test(self,
v)` and `generate(self)` functions described previously.

Let's look back at our example of the point in 2D space and turn this
into a type.

``` python
from paranoid.decorators import accepts, returns, paranoidclass
from paranoid.types import Self, Number, Boolean

@paranoidclass
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    @accepts(Self, Number, Number, Number, Number)
    @returns(Boolean)
    def is_in_box(self, xmin, xmax, ymin, ymax):
        if self.x > xmin and \
           self.x < xmax and \
           self.y > ymin and \
           self.y < ymax:
            return True
        return False
    @staticmethod
    def _test(v):
        assert v.x in Number(), "Invalid X coordinate"
        assert v.y in Number(), "Invalid Y coordinate"
    @staticmethod
    def _generate():
        yield Point(0, 0)
        yield Point(1, 4/7)
        yield Point(-10, -1.99)
```

Types based on classes do not override the `in` syntax.

    >>> Point._test(Point(3, 4))
    >>> Point._test(Point(3, "4"))
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "<stdin>", line 18, in _test
    AssertionError: Invalid Y coordinate
    >>> [Point._test(v) for v in Point._generate()]
    [None, None, None]

As you can see, the `_test(v)` function takes a single variable input,
and tests to see if it is a valid member of this class.  Valid
instances of this class should have `self.x` and `self.y` values which
are numbers.  It would not be valid to use a string for an x position.

Likewise, the `_generate()` function yields valid instances of this
class.

Unlike when we create types from scratch, we do **not** pass the
`self` argument to these functions because they are static methods.
This is because the type is defined based on the class, not based on
the instance of the class.

Using this syntax makes these types valid for all argument and return
types.  For example, we can define a function which takes Points as
arguments and returns a Point:

```python
@accepts(Point, Point)
@returns(Point)
def midpoint(p1, p2):
    xmid = p2.x + (p1.x - p2.x)/2
    ymid = p2.y + (p1.y - p2.y)/2
    return Point(xmid, ymid)
```

Running the standard tests on this, we see:

    >>> mp = midpoint(Point(0, 0), Point(1, 2))
    >>> mp.x, mp.y
    (0.5, 1.0)
    >>> midpoint(3, 5)
    Traceback (most recent call last):
      ...
    paranoid.exceptions.ArgumentTypeError: Invalid argument type: p1=3 is not of type Generic(<class '__main__.Point'>) in midpoint
    >>> [Point._test(midpoint(v1, v2)) \
           for v1 in Point._generate() for v2 in Point._generate()]
    [None, None, None, None, None, None, None, None, None]

## Automated testing

As you can see from many of the examples given here, it makes sense to
test functions by generating values to pass to the function using the
`accepts` type information, and checking that the return values fit
the `returns` type information.  Indeed, Paranoid Scientist will
automate this process.

Basic automatic unit-test--like functionality is available in Paranoid
Scientist.  To use this feature on a file "myfile.py", run the
following at the command line:

    $ python3 -m paranoid myfile.py

This will look through the file at each function containing "accepts"
annotations, and generate a number of test cases for each function to
ensure that the function doesn't fail, and ensure that it satisfies
the "returns"/"ensures" exit conditions.

This should **not** be used as a replacement for unit tests.

## Entry conditions

In addition to the `accepts` and `returns` conditions, we can also
specify more complex relationships among variables.  No type can
define interactions between multiple variables.  For this, we can use
the `requires` operator to specify entry conditions.  This takes a
string of valid Python describing the relationship between the
variables.

Consider for instance the following:

``` python
from paranoid.decorators import accepts
from paranoid.types import Number

@accepts(Number, Number)
def invert_difference(x, y):
    return 1/(x-y)
```

As you can see, this function is not defined when x and y are equal to
each other.  There is no way to define types for x and y without
taking into account their values.  Instead, Paranoid Scientist allows
us to write:

``` python
from paranoid.decorators import accepts, requires
from paranoid.types import Number

@accepts(Number, Number)
@requires("x != y")
def invert_difference(x, y):
    return 1/(x-y)
```

It is also possible to use the `requires` decorator to simplify highly
redundant types.  For example, we could write:

``` python
from paranoid.decorators import accepts, requires
from paranoid.types import Number

@accepts(Number)
@requires("x != 0")
def invert(x):
    return 1/x
```

There is no type that means "all numbers except zero".  While it would
be possible to create such a type for the purposes of this function,
it would start to get messy very quickly to have distinct but nearly
identical types for each function. It is more practical in this
example to put a constraint on the function's domain using the
`requires` condition.

Automated tests will only test functions if their entry conditions are
satisfied.

## Exit conditions

In addition to entry conditions, it is also possible to specify exit
conditions in a similar manner.  Exit conditions are notated similarly
to entry conditions (i.e. Python code inside a string) using the
`ensures` decorator, and specify what must hold after the function
executes.  Exit conditions use the magic variable "return" to describe
how the arguments must relate to return values.  For example,

``` python
from paranoid.decorators import accepts, returns, ensures
from paranoid.types import Number, List

@accepts(List(Number))
@returns(Number)
@ensures('min(l) < return < max(l)')
def mean(l):
    return sum(l)/len(l)
```

    >>> mean([1, 3, 2, 4])
    2.5
    >>> mean([1, 1, 1, 1])
    Traceback (most recent call last):
        ...
    paranoid.exceptions.ExitConditionsError: Ensures statement 'min(l) < return < max(l)' failed in mean
    params: {'l': [1, 1, 1, 1], '__RETURN__': 1.0}

For convenience, exit conditions also allow two new pseudo-operators,
`-->` and `<-->`, which mean "if" and "if and only if" respectively.
For example,

``` python
from paranoid.decorators import accepts, returns, ensures
from paranoid.types import Number

@accepts(Number)
@returns(Number)
@ensures('return == 0 <--> x == 0')
def quadratic(x):
    return x*x
```

Among the four types of conditions which can be imposed upon functions
(argument types, return types, entry conditions, and exit conditions),
exit conditions are unique in that they can also use *previous* values
from a function's execution to test more complex properties of the
function.

In order to use a previous value within exit conditions, add a
backtick after the variable name, e.g. `x` is the current value and
`x\`` is any previous value of x.  (The pneumonic for this is $$x$$
for the variable and $$x'$$ for previous values as might be written in
a universal quantifier, e.g. $$\forall x,x' \in S : \ldots$$.

Why is this useful?  Now, we can test complex properties like a
function's monotonicity:

``` python
from paranoid.decorators import accepts, returns, ensures
from paranoid.types import Number

@accepts(Number)
@returns(Number)
@ensures("x > x` --> return >= return`")
def monotonic(x):
    return x**3
```

## License

All code is available under the MIT license.  See LICENSE.txt for more
information.

## Conceptual FAQs

### Is Paranoid Scientist only for scientific code?

Paranoid Scientist was created with scientific code in mind.
Therefore, design decisions have focused on the idea that incorrect
behavior is infinitely worse than exiting with a runtime error.  The
main implication for this is that there is no exception handling;
errors cause the program to crash.  It is not only unnecessary, but
also very undesirable, to handle errors automatically in scientific
code.  If they are handled incorrectly, the result of the program
could be incorrect. It is better to kill the program and let an expert
analyze and fix the problem.

There are many places where it is important to have correct code, and
Paranoid Scientist is only applicable to a small subset of them.  **Do
not** use it to steer a car, operate a laparoscope, or control a
nuclear reactor.  **Do** use it to increase your confidence that your
data analysis or computational model is not giving incorrect results
due to software bugs.

### So if I just want to reduce the number of bugs in my code, Paranoid Scientist is useless?

Paranoid Scientist may also be used as a development tool.  Keeping it
enabled at runtime probably not the best choice for user-facing
software, but it can still be useful to catch bugs early by, e.g.,
using it only as a contract-oriented programming library for Python.
However, there are better tools for this job.

Also, just to state this explicitly, do **not** use the
automatically-generated test cases as a replacement for unit tests.

### Is Paranoid Scientist fast?

No.  Depending on which options you enable, which features you use,
and how your code is written, your code will run 10%--1000% slower.
The biggest culprits for slow runtime in Paranoid Scientist are
verification conditions involving more than one variable
(e.g. `return\`\``), asserting arguments are immutable, and functions
with many arguments.

However, Paranoid Scientist can easily be enabled or disabled at
runtime with a single line of code.  When it is disabled, there is no
performance loss.  Additionally, the automated unit tests described
above may still be run when it is disabled at runtime.

### How is Paranoid Scientist different from MyPy?

MyPy is an optional static typing system for Python, and aims to
answer the question: "If I run this script, will it succeed?"  Thus,
it is a static analyzer which can find several bugs before they arise
in production environments.

By contrast, Paranoid Scientist answers the question "If I already ran
this script, was the result I received correct?"  It does not do
static analysis, but rather makes the program crash if it detects
potential problems.

Due to these different goals, the main practical difference is that
MyPy emphasizes the machine-readable Python type of a variable,
whereas ParanoidScientist emphasizes the human-understandable type.
Consider the following example of MyPy, which comes directly from the
[MyPy website](http://mypy-lang.org/examples.html):

```python
class BankAccount:
    def __init__(self, initial_balance: int = 0) -> None:
        self.balance = initial_balance
    def deposit(self, amount: int) -> None:
        self.balance += amount
    def withdraw(self, amount: int) -> None:
        self.balance -= amount
    def overdrawn(self) -> bool:
        return self.balance < 0

my_account = BankAccount(15)
my_account.withdraw(5)
print(my_account.balance)
```

You can see how this bank account system is convenient because it
ensures that the amount withdrawn or deposited always is an integer.
However, what would happen if you ran the following code?

    >>> my_account.deposit(-5)

Using this, you can withdraw money using the deposit function!

By contrast, using Paranoid Scientist on this code block would look
like the following:

```python
from paranoid.decorators import accepts, requires, paranoidclass
from paranoid.types import Natural1, Self

@paranoidclass
class BankAccount:
    @staticmethod
    def _test(v):
        assert v.balance >= 0
    @staticmethod
    def _generate():
        yield BankAccount(0)
        yield BankAccount(10)
    def __init__(self, initial_balance = 0):
        self.balance = initial_balance
    @accepts(Self, Natural1)
    def deposit(self, amount):
        self.balance += amount
    @accepts(Self, Natural1)
    @requires('self.balance >= amount')
    def withdraw(self, amount):
        self.balance -= amount

my_account = BankAccount(15)
my_account.withdraw(5)
print(my_account.balance)
```

    >>> my_account.deposit(-5)
    Traceback (most recent call last):
        ...
    paranoid.exceptions.ArgumentTypeError: Invalid argument type: amount=-5 is not of type <paranoid.types.numeric.Natural1 object at 0x7fd1e5bcc7b8> in BankAccount.deposit

Note that this also obviates the need for the "overdrawn" function,
because it will never allow an operation on a bank account which would
overdraft.

    >>> my_account.withdraw(1000)
    Traceback (most recent call last):
        ...
    paranoid.exceptions.EntryConditionsError: Function requirement 'self.balance >= amount' failed in BankAccount.withdraw

Nevertheless, MyPy is an excellent library, but it accomplishes
different goals than Paranoid Scientist.

### How does Paranoid Scientist differ from using contracts (e.g. PyContracts)?

- Contracts do not allow the comparison of previous executions of a
  function.  Therefore, you cannot reason about higher level
  properties of a function, such as monotonicity or concavity.
- Contracts cannot perform automated testing.
- PyContracts does not allow parameterized contracts other than the
  defaults.

### Is Paranoid Scientist "Pythonic"?

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

## Technical FAQs

### How do I use Paranoid Scientist in my code?

At the top of each source file, include the line

```python
import paranoid as pns
```

in each source file.  Then, to access functions types, simply refer to
them as `pns.Range(0,1)` or `@pns.accepts(pns.Number)`.  Optionally,
you may want to include

```python
from paranoid import accepts, returns, requires, ensures, paranoidclass, paranoidconfig
```

for easy access to the function decorators.

### Why are Python lists and numpy 1D arrays different types?

These types behave differently in many common situation which can lead
to bugs.  For instance, consider the following function:

```python
def add_lists(a, b):
    return a + b
```

Does this concatenate the lists or does it perform element-wise
addition?  The answer depends on the datatype passed.

### Why are Numpy numbers and Python numbers the same type?

As you may know, integers and floats in Python are different from
integers and floats in Numpy.  While both behave similarly in most
circumstances, Paranoid Scientist treats these as the same type.
Numpy claims that their numeric type system is fully compatible with
Python's, however there are subtle differences.

The biggest difference for Paranoid Scientist is that Numpy integer
types can overflow whereas Python types do not.  Paranoid Scientist
approaches this by forcing numpy to throw an error if there is an
overflow.

There are some differences which are not addressed by this.  For
example, there are certain operations are only suppored on one of the
two types, and certain situations where Numpy types do not pickle
properly.  If either of these situations arise, it is straightforward
to define a new type which only supports either Numpy or non-Numpy
types.  In most situations, it is expected that the default behavior
will suffice.

### What types are included by default?

- Numeric types:
    - Numeric: Any real number, plus inf/-inf/nan.
    - ExtendedReal: Any real number plus inf/-inf.
    - Number: Any real number.
    - Integer: An integer.
    - Natural0: A natural number including 0.
    - Natural1: A natural number starting with 1.
    - Range(x,y): A number in the interval [x,y].
    - RangeClosedOpen(x,y): A number in the interval [x,y).
    - RangeOpenClosed(x,y): A number in the interval (x,y].
    - RangeOpen(x,y): A number in the range (x,y).
    - Positive0: A positive number or zero.
    - Positive: A positive number excluding zero.
    - NDArray(d=None, t=None): A Numpy NDArray.  Optionally, require
      it to have `d` dimensions.  Optionally, require elements of the
      array to be of type `t` (which can be any Paranoid type).
- Other:
    - Unchecked(t=None): Do not check the type for this element.
      Optionally, a Paranoid type `t` can be passed as a type to
      generate during automated testing (to allow testing of functions
      of unchecked type).
    - Constant(v): Can only be the value `v`.
    - Self: A special type to use inside classes for the `self` argument.
    - Nothing: Can only be None.
    - Function: Any Python function.
    - Boolean: Either True or False.
    - And(t1, t2, ...): Any number of Paranoid types may be passed as
      arguments.  Require a value to satisfy all of these types.
    - Or(t1, t2, ...): Any number of Paranoid types may be passed as
      arguments.  Require a value to satisfy at least one of these
      types.
    - Not(t): Can be anything other than the Paranoid type `t`.
- Collections:
    - Set(els): The argument `els` should be a list of accepted
      values.  This is equivalent to an enum.  For example,
      Set([0, 1, 2, 3]) accepts only these four numbers.
    - List(t): A Python list with elements of Paranoid type `t`
    - Dict(k, v): A Python dictionary where keys have Paranoid type
      `k` and values have Paranoid type `v`.
- Strings:
    - String: Any string.
    - Identifier: Any non-empty string containing only alpha-numeric
      characters plus underscores and hyphens.
    - Alphanumeric: Any non-empty alphanumeric string.
    - Latin: Any non-empty string with Latin characters only.
