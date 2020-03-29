.. Paranoid Scientist documentation master file, created by
   sphinx-quickstart on Fri Apr  6 07:46:42 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Paranoid Scientist
==================

.. image:: images/paranoid_scientist_logo.png
   :class: align-right
   :width: 30%

Paranoid Scientist is a Python module for verifying scientific
software which provides:

- Runtime **verification of entry and exit conditions** written in
  pure Python, including hyperproperties.
- Conditions specified using pure Python **refinement types**,
  i.e. types are defined by predicates.
- **Automated unit testing** of individual functions.

It is inspired by `contract-oriented programming
<conceptfaq.html#how-does-paranoid-scientist-differ-from-using-contracts-e-g-pycontracts>`_,
type classes, `static type checking
<conceptfaq.html#how-is-paranoid-scientist-different-from-mypy>`_, and
fuzz testing.

To learn more, read the :ref:`tutorial<Tutorial>` or check out the
:ref:`conceptual FAQs<Conceptual FAQs>` or :ref:`technical
FAQs<Technical FAQs>`.  Also see the `paper
<https://link.springer.com/chapter/10.1007%2F978-3-030-41600-3_10>`_
or `preprint <https://arxiv.org/abs/1909.00427>`_ for more technical
details.

Why verify scientific software?
-------------------------------

Paranoid Scientist is a tool to make sure scientific code is correct.
Verification is extremely important for scientific software because,
unlike most software, we don't know what the output will be until we
run the program.  In fact, the program is written in order to examine
the output. However, we have no robust way of knowing whether the
output is due to a software bug.  For example, code performing a
complex statistical test could normalize the wrong column, an error
which would likely go undetected.

Paranoid Scientist attempts to remedy this situation by providing some
key tools from the software verification community to the scientific
community.  Traditional program verification asks the question, "If I
run my code, will it run correctly?"  In practice, this is time
consuming and requires highly specialized training.  For scientific
programming, it is acceptable to instead ask, "If I already ran my
code, did it run correctly?"  In other words, it is not as important
to know before executing the program whether it will run correctly.
Paranoid Scientist is already in use in scientific software.

Quick examples
--------------

Paranoid Scientist is used to programmatically define and verify
function entry and exit conditions.  Here are some simple examples::

Cube a number
~~~~~~~~~~~~~

We ensure that the "cube" function accepts and returns numbers
(i.e. integers or floats, but not NaN or ±inf), and that it is
monotonic::

  from paranoid.types import Number
  from paranoid.decorators import accepts, returns, ensures
  @accepts(Number)
  @returns(Number)
  @ensures("x >= x` --> return >= return`") # Test for monotonicity
  def cube(x):
      return x**3

Running this function for correct and incorrect input, we get::

  >>> cube(3)
  27
  >>> import math
  >>> cube(math.nan)
  Traceback (most recent call last):
  ...
  paranoid.exceptions.ArgumentTypeError: Invalid argument type: x=nan is not of type Number in cube

Biased coin
~~~~~~~~~~~

We can also verify stochastic functions.  Suppose we perform `flips`
flips of a biased coin which has a `p_heads` probability of showing
heads.  How many times do we get heads?

The argument `flips` must be a natural number greater than zero, and
`p_heads` must be a number between 0 and 1 inclusive.  This must
return a natural number greater than or equal to zero.  Additionally,
we check that the number of heads returned must always be less than or
equal to the number of flips, and that if our probability of getting
heads is zero, then we don't get any heads::

  from paranoid.types import Natural0, Natural1, Range
  from paranoid.decorators import accepts, returns, ensures
  import random
  @accepts(Natural1, Range(0, 1))
  @returns(Natural0)
  @ensures("return <= flips")
  @ensures("p_heads == 0 --> return == 0")
  def biased_coin(flips, p_heads=0.5):
      return sum([random.random() < p_heads for _ in range(flips)])

Running several examples, we see::

  >>> biased_coin(3, 1)
  3
  >>> biased_coin(3, 1+1e50)
  Traceback (most recent call last):
  ...
  paranoid.exceptions.ArgumentTypeError: Invalid argument type: p_heads=1e+50 is not of type Range(0, 1) in biased_coin

More examples
~~~~~~~~~~~~~

For more more realistic toy examples, see examples in the `paper
<https://link.springer.com/chapter/10.1007%2F978-3-030-41600-3_10>`_
or `preprint <https://arxiv.org/abs/1909.00427>`_.  To see Paranoid
Scientist in action, see `PyDDM
<https://pyddm.readthedocs.io/en/latest/>`_ or `Matplotlib Canvas
<https://github.com/mwshinn/canvas>`_.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   index
   tutorial
   installation
   conceptfaq
   techfaq
   api/index

