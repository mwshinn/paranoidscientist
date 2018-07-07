Technical FAQs
==============

How do I use Paranoid Scientist in my code?
-------------------------------------------

At the top of each source file, include the line::

  import paranoid as pns

in each source file.  Then, to access functions types, simply refer to
them as ``pns.Range(0,1)`` or ``@pns.accepts(pns.Number)``.  Optionally,
you may want to include::

  from paranoid import accepts, returns, requires, ensures, paranoidclass, paranoidconfig

for easy access to the function decorators.

Why are Python lists and numpy 1D arrays different types?
---------------------------------------------------------

These types behave differently in many common situation which can lead
to bugs.  For instance, consider the following function::

  def add_lists(a, b):
      return a + b

Does this concatenate the lists or does it perform element-wise
addition?  The answer depends on the datatype passed.

Why didn't you use Python's built-in type syntax?
-------------------------------------------------

In Python's built-in type syntax, it is not possible to check for
entry and exit conditions which depend on more than one function
argument.  In order to support this, decorator notation would need to
be used as well.  In order to maintain consistency, everything uses
decorator notation.

Why are Numpy numbers and Python numbers the same type?
-------------------------------------------------------

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
example, there are certain operations are only supported on one of the
two types, and certain situations where Numpy types do not pickle
properly.  If either of these situations arise, it is straightforward
to define a new type which only supports either Numpy or non-Numpy
types.  In most situations, it is expected that the default behavior
will suffice.

Why don't NDArrays or lists have an optional length parameter?
--------------------------------------------------------------

A very common paradigm is to require that a list (array) argument has
the same length (shape) as another argument or as the return value.
However, types must be independent of each other, and so such a
dependency is not possible.  These must be checked in an ``@ensures``
statement rather than within the type itself.

While there are certainly use cases for lists and arrays of a
particular fixed length, to avoid confusion with this common use case
and reduce the complexity of NDArray specifications, these must be
checked in ``@ensures`` statements as well.

I can think of a counter-example where Paranoid Scientist would fail!
---------------------------------------------------------------------

That's not a question.  And so can we.  An easy example is subclassing
int and redefining ``__add__`` or ``__radd__``.  However, if you are
subclassing int, you clearly know what you are doing and should know
that this will cause many things to fail in general.

If you come across an example in production code where Paranoid
Scientist's type system becomes misleading, if the example is
not rare or contrived, please report this as a bug.
