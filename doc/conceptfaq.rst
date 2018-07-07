Conceptual FAQs
===============

Is Paranoid Scientist only for scientific code?
-----------------------------------------------

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

So if I just want to reduce the number of bugs in my code, Paranoid Scientist is useless?
-----------------------------------------------------------------------------------------

Paranoid Scientist may also be used as a development tool.  Keeping it
enabled at runtime probably not the best choice for user-facing
software, but it can still be useful to catch bugs early by, e.g.,
using only the contract-oriented programming features.

Also, just to state this explicitly, do **not** use the
automatically-generated test cases as a replacement for unit tests.
All code should be thoroughly tested.  While Paranoid Scientist can
help and is much better than nothing, it is not by itself sufficient.

Is Paranoid Scientist fast?
---------------------------

No.  Depending on which options you enable, which features you use,
and how your code is written, your code will run 10%--1000% slower.
The biggest culprits for slow runtime in Paranoid Scientist are
verification conditions involving more than one variable
(e.g. ``return```) and functions with many arguments.

However, Paranoid Scientist can easily be enabled or disabled at
runtime with a single line of code.  When it is disabled, there is no
performance loss.  Additionally, the automated unit tests described
above may still be run when runtime checking is disabled.

Additionally, runtime verification of some essential functions
(e.g. those that are called inside a loop) may be explicitly disabled.
To disable runtime checking for a single function, set
``enabled=False`` using the ``@paranoidconfig`` decorator::

  from paranoid.decorators import accepts, returns, paranoidconfig
  @accepts(Number)
  @returns(String)
  @paranoidconfig(enabled=False)
  def slow_function(x):
      return run_slow_stuff(x)

Alternatively, Paranoid Scientist can be disabled globally using::

  from paranoid.settings import Settings
  Settings.set(enabled=False)

How is Paranoid Scientist different from MyPy?
----------------------------------------------

MyPy (and Pyre) provide an optional static typing system for Python,
and aim to answer the question: "If I run this program, will it
succeed?"  Thus, it is a static analyzer which can find several bugs
before they arise in production environments.

By contrast, Paranoid Scientist answers the question "If I already ran
this program, was the result I received correct?"  It does not do
static analysis, but rather makes the program crash if it detects
potential problems.

Due to these different goals, the main practical difference is that
MyPy emphasizes the machine-readable Python type of a variable,
whereas ParanoidScientist emphasizes the human-understandable type.
Consider the following example of MyPy, which comes directly from the
`MyPy website <http://mypy-lang.org/examples.html>`_::

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

You can see how this bank account system is convenient because it
ensures that the amount withdrawn or deposited always is an integer.
However, what would happen if you ran the following code::

  >>> my_account.deposit(-5)

Using this, you can withdraw money using the deposit function!

By contrast, using Paranoid Scientist on this code block would look
like the following::

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

Then when we run it, we get the following::
  
  >>> my_account.deposit(-5)
  Traceback (most recent call last):
      ...
  paranoid.exceptions.ArgumentTypeError: Invalid argument type: amount=-5 is not of type <paranoid.types.numeric.Natural1 object at 0x7fd1e5bcc7b8> in BankAccount.deposit

Note that this also obviates the need for the "overdrawn" function,
because it will never allow an operation on a bank account which would
overdraft::

  >>> my_account.withdraw(1000)
  Traceback (most recent call last):
      ...
  paranoid.exceptions.EntryConditionsError: Function requirement 'self.balance >= amount' failed in BankAccount.withdraw

Nevertheless, MyPy is an excellent library, but it accomplishes
different goals than Paranoid Scientist.

How does Paranoid Scientist differ from using contracts (e.g. PyContracts)?
---------------------------------------------------------------------------

Contracts in theory implement several of the same features but are
conceptually distinct:

- Paranoid Scientist emphasizes the type of each function argument
  whereas contracts do not
- Paranoid Scientist only defines the entry and exit conditions,
  whereas contracts often define other features of functions such as
  exceptions that may be raised
- Paranoid Scientist is most concerned with humans being able to
  understand the entry and exit conditions at a glance, whereas
  contracts do not have this focus.

These properties give Paranoid Scientist a few unique features which
are either awkward or impossible with contracts:

- Unlike contracts, Paranoid Scientist allows comparison of function
  arguments with previous executions of a function.  Therefore, you
  can reason about higher level properties of a function, such as
  monotonicity or concavity.
- Paranoid Scientist can perform automated testing, whereas contracts
  cannot

Is Paranoid Scientist "Pythonic"?
---------------------------------

While the concept of types are generally considered non-Pythonic,
Paranoid Scientist's types can be thought of as the duck typed type
system.

In general, Pythonic code relies on duck typing, which is great in
many situations but increases the probability of undetected bugs.  As
an example, consider the following::

  M = get_data_as_matrix()
  M_squared = M**2
  print(M_squared.tolist())

What is the result of this computation?  Duck typing tells us that we
have squared the matrix, but this does not necessarily tell us which
computation was performed. If we look more closely, the result depends
on the matrix type returned by `get_data_as_matrix`::

  M = numpy.matrix([[1, 2], [3, 4]])
  M_squared = M**2
  print(M_squared.tolist())
  
  M = numpy.array([[1, 2], [3, 4]])
  M_squared = M**2
  print(M_squared.tolist())
  
which outputs::

  [[7, 10], [15, 22]]
  [[1, 4], [9, 16]]

As we can see, the result of this computation depends on whether the
matrix is a numpy array or a numpy matrix, both of which are common
datatypes in practice.  The former implement element-wise
multiplication, while the latter implements matrix multiplication.
Forgetting to cast an array to a matrix (or vice versa) can introduce
subtle bugs into your code that could easily go undetected.

By contrast, the type system in Paranoid Scientist only mandates that
types act like some specific concept which is understandable to humans
in particular situations.  For example, if it looks like a Number and
quacks like a Number, then it doesn't matter whether the underlying
datatype is a float or an int.
