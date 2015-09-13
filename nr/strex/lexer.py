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
nr.strex.lexer
==============

This module provides a simple facility for tokenizing character streams::

    from nr.strex.rules import Ruleset, Charset, Regex
    from nr.strex.lexer import Lexer
    from nr.strex.scanner import Scanner
    from string import whitespace, ascii_letters, digits

    rules = Ruleset()
    rules.add('ws', Charset(whitespace))
    rules.add('id', Charset(ascii_letters))
    rules.add('op', Regex('\*|\+|\-|/'))
    rules.add('number', Regex('\d+(\.\d+)?'))
    rules.skip('ws')
    lexer = Lexer(Scanner('x * a + 2 * b + c'), rules)
    print([(t.type, t.value) for t in lexer])

    # [('id', 'x'), ('op', '*'), ('id', 'a'), ('op', '+'), ('number', '2'),
    #  ('op', '*'), ('id', 'b'), ('op', '+'), ('id', 'c'), ('eof', None)]

The special token type ``'eof'`` is reserved for tokens that represent
the end of the token stream. :meth:`Ruleset.iter_tokens` will not yield
such a token, but the :class:`Lexer` class will create one after the
token generator has finished. Usually, the line and column number of
EOF tokens are set to zero.
'''

eof = 'eof'


class Token(object):
    '''
    This class represents a token from a character stream. The end
    of the stream is represented by a Token of :attr:`type` ``'eof'``.
    If a character could not be handled, it is represented by a Token
    of :attr:`type` :const:`None` and is called an unhandled Token.
    '''

    def __init__(self, type_, value, lineno, colno=None):
        if isinstance(lineno, tuple):
            if colno is not None:
                raise TypeError('colno must not be given when '
                                'lineno is Scanner.state() result')
            lineno, colno = lineno[1], lineno[2]
        elif not isinstance(lineno, int):
            raise TypeError('lineno must be Scanner.state() result or int')

        self.type = type_
        self.value = value
        self.lineno = lineno
        self.colno = colno

    def __repr__(self):
        fmt = (self.type, self.value, self.lineno, self.colno)
        if self.eof():
            return '<Token EOF at line:{} col:{}>'.format(*fmt[2:])
        elif not self.handled():
            return '<Token UNHANDLED:{!r} at line:{} col:{}>'.format(*fmt[1:])
        else:
            fmt += ('' if self.valid() else ' INVALID',)
            return '<Token {!s}:{!r} at line{} col:{}{}>'.format(*fmt)

    def handled(self):
        return self.type is not None

    def valid(self):
        return not self.handled()

    def eof(self):
        return self.type == eof


class Lexer(object):
    '''
    Convenient wrapper for the :meth:`Ruleset.iter_tokens` generator
    to process tokens. Creates an EOF Token at the end of the stream.
    '''

    def __init__(self, scanner, ruleset):
        self.scanner = scanner
        self.ruleset = ruleset
        self.token = None
        self.next()

    def __bool__(self):
        return not self.token.eof()

    __nonzero__ = __bool__

    def __iter__(self):
        while not self.token.eof():
            yield self.token
            self.next()

    def next(self):
        token = self.token
        if token is not None and token.eof():
            return token

        token = None
        scanner = self.scanner
        ruleset = self.ruleset

        while token is None:
            state = scanner.state()
            if not scanner:
                token = Token(eof, None, state)
                break

            for __, type_, rule in ruleset.rules:
                value = rule.match(scanner)
                if value:
                    token = rule.make_token(type_, value, state[1], state[2])
                    break
                scanner.restore(state)

            if token is None:
                token = Token(None, scanner.char, state)
                scanner.next()
            elif state == scanner.state():
                msg = "rule yielded token without moving scanner"
                raise RuntimeError(msg)

            if token.type in ruleset.skips:
                token = None

        self.token = token
        return token


from nr.strex.rules import Rule
