Paranoid Scientist
==================

Paranoid Scientist is a Python module which allows runtime
verification of entry and exit conditions for Python functions using a
novel type system which prioritizes the interpretation of types over
their representation.  It is intended for scientific software.  More
specifically, it provides the following:

- A **novel type system**, which emphasizes the *meaning* of the type
  instead of the *data structure* of the type.
- Verification of arbitrary **entry and exit conditions**, including more
  complex expressions with universal quantification.
- **Automated testing** of individual functions to determine, before
  execution of the program, whether functions conform to their
  specification.
- A simple and clear function decorator notation

See the
[documentation](http://paranoid-scientist.readthedocs.io/en/latest/),
[conceptual FAQs](http://paranoid-scientist.readthedocs.io/en/latest/conceptfaq.html),
[technical FAQs](http://paranoid-scientist.readthedocs.io/en/latest/techfaq.html),
or
[tutorial](http://paranoid-scientist.readthedocs.io/en/latest/tutorial.html)
for more information.


## System requirements

- Python 3.5 or above
- Optional: Numpy (for Numpy types support)


## License

All code is available under the MIT license.  See LICENSE.txt for more
information.


## What types are included by default?

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
