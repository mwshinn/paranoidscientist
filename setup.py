# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

from distutils.core import setup

setup(
    name = 'ParanoidScientist',
    version = '1.0',
    description = 'Runtime verification and automated testing for scientific code',
    author = 'Max Shinn',
    author_email = 'maxwell.shinn@yale.edu',
    maintainer = 'Max Shinn',
    license = 'MIT',
    maintainer_email = 'maxwell.shinn@yale.edu',
    packages = ['paranoid', 'paranoid.types'],
    #py_modules = ['paranoid', 'paranoid.exceptions', 'paranoid.decorators', 'paranoid.types', 'paranoid.utils', 'paranoid.types.base', 'paranoid.types.collections', 'paranoid.types.numeric', 'paranoid.types.string'],
    #requires = ['numpy']
)
