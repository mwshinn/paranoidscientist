# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

__all__ = ["String", "Identifier", "Alphanumeric", "Latin"]
import re
from .base import Type

class String(Type):
    """Any string."""
    def test(self, v):
        super().test(v)
        assert isinstance(v, str), "Non-string passed"
    def generate(self):
        yield "" # Empty string
        yield "a" # A short string
        yield "a"*1000 # A long string
        yield " " # A whitespace string
        yield "abc123" # An alphanumeric string
        yield "Two words sentence." # A sentence-like string
        yield "\\" # An escape sequence string
        yield "%s" # An substitution pattern string
        yield "2" # A string which can be interpreted as a number
        yield "баклажан" # A UTF-8 string

class Identifier(String):
    """Any non-empty alphanumeric string with underscores and hyphens."""
    is_ident = re.compile(r'^[A-Za-z0-9_-]+$')
    def test(self, v):
        super().test(v)
        assert self.is_ident.match(v), "Invalid identifier characters"
    def generate(self):
        yield "_" # Empty string
        yield "-" # Empty string
        yield "a" # A short string
        yield "a"*1000 # A long string
        yield "abc123" # An alphanumeric string
        yield "2" # A string which can be interpreted as a number
        yield "test_underscore" # A string with an undescrore
        yield "test-underscore" # A string with a hyphen
        yield "-hyphenstart" # A string starting with a hyphen
        yield "_undescorestart" # A string starting with an underscore
        yield "hyphenend-" # A string ending with a hyphen
        yield "undescoreend-" # A string ending with an underscore

class Alphanumeric(Identifier):
    """Any non-empty alphanumeric string"""
    is_alphanum = re.compile(r'^[A-Za-z0-9]+$')
    def test(self, v):
        super().test(v)
        assert self.is_alphanum.match(v), "Invalid alphanumeric characters"
    def generate(self):
        yield "a" # A short string
        yield "a"*1000 # A long string
        yield "abc123" # An alphanumeric string
        yield "2" # A string which can be interpreted as a number

class Latin(Alphanumeric):
    """Any non-empty string with latin characters only"""
    is_lat = re.compile(r'^[A-Za-z]+$')
    def test(self, v):
        super().test(v)
        assert self.is_lat.match(v), "Invalid latin characters"
    def generate(self):
        yield "a" # A short string
        yield "P" # A capital leter
        yield "tree" # A word
        yield "TfadFftsF" # A mixed case word
        yield "a"*1000 # A long string

