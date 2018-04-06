Technical FAQs
==============

How do I use Paranoid Scientist in my code?
-------------------------------------------

At the top of each source file, include the line::

  import paranoid as pns

in each source file.  Then, to access functions types, simply refer to
them as `pns.Range(0,1)` or `@pns.accepts(pns.Number)`.  Optionally,
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
example, there are certain operations are only suppored on one of the
two types, and certain situations where Numpy types do not pickle
properly.  If either of these situations arise, it is straightforward
to define a new type which only supports either Numpy or non-Numpy
types.  In most situations, it is expected that the default behavior
will suffice.
