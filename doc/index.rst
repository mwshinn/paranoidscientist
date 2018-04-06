.. Paranoid Scientist documentation master file, created by
   sphinx-quickstart on Fri Apr  6 07:46:42 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

What is Paranoid Scientist
==========================

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

Quick example
-------------

Paranoid Scientist is used to programmatically define and verify
function entry and exit conditions.  Here are some simple examples::

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


What is the point?
------------------

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



.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   tutorial
   conceptfaq
   techfaq
   api/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
