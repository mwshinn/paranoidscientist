Installation
============

System requirements
-------------------

- Python 3.5 or above
- Optional: Numpy (for Numpy types support)

Installation
------------

Normally, you can install with::

    pip install paranoid-scientist

If you are in a shared environment (e.g. a cluster), install with::

    pip install paranoid-scientist --user

If installing from source, download, extract, and do::

    python3 setup.py install


Getting the source
------------------

`Source code available on Github <https://github.com/mwshinn/paranoidscientist>`_.

Testing
-------

To ensure that everything works as expected, on unix systems, run::

    ./runtests.sh

or on Windows, run::

  python3 -m paranoid tests/testauto.py
  python3 tests/tests.py
