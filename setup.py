# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

from setuptools import setup

from paranoid._version import __version__

with open("README.md", "r") as f:
    long_desc = f.read()

setup(
    name = 'paranoid-scientist',
    version = __version__,
    description = 'Runtime verification and automated testing for scientific code',
    long_description = long_desc,
    long_description_content_type='text/markdown',
    author = 'Max Shinn',
    author_email = 'maxwell.shinn@yale.edu',
    url = 'https://github.com/mwshinn/paranoidscientist',
    maintainer = 'Max Shinn',
    license = 'MIT',
    python_requires='>=3.5',
    maintainer_email = 'maxwell.shinn@yale.edu',
    packages = ['paranoid', 'paranoid.types'],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Education :: Testing',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing']
)
