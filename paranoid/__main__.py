# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

import sys
import re
from io import StringIO
from contextlib import redirect_stdout
from .testfunctions import test_function

# If called as "python3 -m verify script_file_name.py", then unit test
# script_file_name.py.  By this, we mean call the function
# test_function on each function which has annotations.  Note that we
# must execute the entire file script_file_name.py in order to do
# this, so any time-intensive code should be in a __name__ ==
# "__main__" guard, which will not be executed.
#
# We know if a function has annotations because all annotations are
# passed through the _decorator function (so that we can ensure we
# only use at most one more stack frame no matter how many function
# annotations we have).  The _decorator function will look for the
# global variable __ALL_FUNCTIONS to be defined within the verify
# module.  If it is defined, it will add one copy of each decorated
# function to the list.  Then, we can perform the unit test by
# iterating through each of these.  This has the advantage of allowing
# nested functions and object methods to be discovered for
# verification.
if __name__ == "__main__":
    # Pass exactly one argement: the python file to check
    # len == 2 if the path to the module is arg 1.
    if not (len(sys.argv) == 2 or (len(sys.argv) == 3 and sys.argv[1] == "-m")):
        exit("Invalid argument, please pass a python file or '-m modulename'")
    # Add the __ALL_FUNCTIONS to the global scope of the verify module
    # and then run the script.  Save the global variables from script
    # execution so that we can find the __ALL_FUNCTIONS variable once
    # the script has finished executing.
    globs = {} # Global variables from script execution
    # Get the script file's text
    if len(sys.argv) == 3:
        script_contents = "import %s\n" % sys.argv[2]
        name = sys.argv[2]
    elif len(sys.argv) == 2:
        script_contents = open(sys.argv[1], "r").read()
        name = sys.argv[1]
    # Include the paranoid code in a predictable way
    prefix = "import paranoid as __paranoidmod;__paranoidmod.decorators.__ALL_FUNCTIONS = [];"
    # Get rid of relative imports
    script_contents = re.sub(r'from\s+\.([A-Za-z0-9_\.]+)\s+import', r'from \1 import', script_contents)
    script_contents = re.sub(r'from\s+\.\s+import', r'import', script_contents)
    # Execute to find the functions and save them.
    exec(prefix + script_contents, globs)
    all_functions = globs["__paranoidmod"].decorators.__ALL_FUNCTIONS
    # Test each function from the script.
    untested = []
    for f in all_functions:
        # Some function executions might take a while, so we print to
        # the screen when we begin testing a function, and then erase
        # it after we finish testing the function.  This is like a
        # make-shift progress bar.
        start_text = "    Testing %s..." % f.__name__
        print(start_text, end="", flush=True)
        pseudo_stdout = StringIO()
        with redirect_stdout(pseudo_stdout):
            ntests = test_function(f)
        stdout = pseudo_stdout.getvalue()
        if len(stdout) == 0: # Erase only if nothing was printed during testing
            print("\b"*len(start_text), end="")
        else:
            print("\n", end="")
            print(stdout, end="")
        # Extra spaces after "Tested %s" compensate for the fact that
        # the string to signal the start of testing function f is
        # longer than the string to signal function f has been tested,
        # so this avoids leaving extra characters on the terminal.
        print("    Tested %i values for %s    " % (ntests, f.__name__), flush=True)
        if ntests == 0:
            untested.append(f.__name__)
    print("Tested %i functions in %s." % (len(all_functions), name))
    if untested:
        print("WARNING: The following functions were untested: %s" % ", ".join(untested))
