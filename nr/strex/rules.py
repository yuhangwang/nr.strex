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

from nr.strex.lexer import Token

import re


class Ruleset(object):

    def __init__(self):
        self.rules = []
        self.skips = set()

    def skip(self, *token_types):
        self.skips |= set(token_types)

    def add(self, type_, rule, priority=0):
        if not isinstance(rule, Rule):
            raise TypeError('Expected Rule instance')
        for index, other_rule in enumerate(self.rules):
            if other_rule[0] < priority:
                break
        else:
            index = len(self.rules)
        self.rules.insert(index, (priority, type_, rule))


class Rule(object):

    def match(self, scanner):
        raise NotImplementedError

    def make_token(self, type_, value, lineno, colno):
        return Token(type_, value, lineno, colno)


class Charset(Rule):

    def __init__(self, charset, at_column=-1):
        self._charset = frozenset(charset)
        self._at_column = at_column

    def match(self, scanner):
        if self._at_column >= 0 and self._at_column != scanner.colno():
            return None
        char = scanner.char
        result = type(char)()
        while char and char in self._charset:
            result += char
            char = scanner.next()
        return result


class Seq(Rule):

    def __init__(self, string, case_sensitive=True):
        self._string = string
        self._case_sensitive = case_sensitive

    def match(self, scanner):
        string = self._string
        if not self._case_sensitive:
            string = string.lower()

        char = scanner.char
        result = type(char)()
        for other_char in self._string:
            if not self._case_sensitive:
                char = char.lower()
            if char != other_char:
                return None
            result += char
            char = scanner.next()

        return result


class String(Rule):
    ''' Parses a quoted sequence of characters. The returned token can
        be invalid, i.e. if there was no closing quote. This can be
        checked with :meth:`Token.valid`. '''

    class StringToken(Token):

        def __init__(self, type_, value, lineno, colno, closed):
            super(String, self).__init__(type_, value, lineno, colno)
            self.closed = closed

        def valid(self):
            return self.closed and super(String, self).valid()

    def __init__(self, single=True, double=True):
        self._single = single
        self._double = double

    def match(self, scanner):
        char = scanner.char
        if (self._single and char == "'") or (self._double and char == '"'):
            quote = char
        else:
            return None

        result = quote
        char = scanner.next()
        while char and char != quote and char != '\n':
            result += char
            if char == '\\':
                char = scanner.next()
                result += char
            char = scanner.next()

        if not char or char == '\n':
            return (False, result)
        else:
            scanner.next()
            result += quote
            return (True, result)

    def make_token(self, type_, value, lineno, colno):
        return String.StringToken(type_, value[1], lineno, colno, value[0])


class Regex(Rule):
    ''' Matches a regular expression. The returned token has a
        ``groups`` attribute that contains the matched groups from
        the expressions result. '''

    class RegexToken(Token):

        def __init__(self, type_, value, lineno, colno, groups):
            super(Regex.RegexToken, self).__init__(type_, value, lineno, colno)
            self.groups = groups

    def __init__(self, regex, flags=0):
        if isinstance(regex, str):
            regex = re.compile(regex, flags)
        self._regex = regex

    def match(self, scanner):
        return scanner.match(self._regex)

    def make_token(self, type_, match, lineno, colno):
        value, groups = match.group(), match.groups()
        return Regex.RegexToken(type_, value, lineno, colno, groups)
