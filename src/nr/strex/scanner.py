# -*- coding: utf-8 -*-
#
# Copyright (C) 2015  Niklas Rosenstein
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
'''
nr.strex.scanner
================

This module provides the :class:`Scanner` class which is a handy utility
to process strings and keeping track of line and column numbers.
'''

import re
import collections

Cursor = collections.namedtuple('Cursor', 'position lineno colno')


class Scanner(object):

    def __init__(self, content):
        self._content = content
        self.position = 0
        self.lineno = 1
        self.colno = 0

    def __repr__(self):
        return '<Scanner at {} line:{} col:{}>'.format(*self.state())

    def __bool__(self):
        return self.position < len(self._content)

    __nonzero__ = __bool__

    def state(self):
        return Cursor(self.position, self.lineno, self.colno)

    def restore(self, state):
        self.position, self.lineno, self.colno = state

    @property
    def char(self):
        if self.position < len(self._content):
            return self._content[self.position]
        else:
            return type(self._content)()

    def next(self):
        char = self.char
        if not char:
            return char
        if char == '\n':
            self.lineno += 1
            self.colno = 0
        else:
            self.colno += 1
        self.position += 1
        return self.char

    def match(self, regex):
        match = regex.match(self._content, self.position)
        if not match:
            return None

        text = match.group()
        lines = text.count('\n')

        self.position = match.end()
        self.lineno += lines
        if lines:
            self.colno = 0
            self.colno = len(text) - text.rfind('\n') - 1
        else:
            self.colno += len(text)

        return match
