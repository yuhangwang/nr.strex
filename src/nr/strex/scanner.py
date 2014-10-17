# -*- coding: utf-8 -*-
#
# Copyright (C) 2014  Niklas Rosenstein
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
"""
strex.scanner - Utilities for string processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module exposes the :class:`Scanner` class which is a handy
tool for processing strings and streams of characters, making it
easy to parse text in any format.
"""

def Universal(stream):
    """
    This function can be passed as value for the *newline* argument
    of the :class:`Scanner` constructor to universally handle newlines.
    Universal newlines support LF and CRLF.
    """

    char = stream.read(1)
    if char == '\r':
        next_char = stream.read(1)
        if next_char == '\n':
            return True
    elif char == '\n':
        return True
    return False

def Linefeed(stream):
    """
    This function can be passed as value for the *newline* argument
    of the :class:`Scanner` constructor to handle only line-feed
    characters as newlines.
    """

    char = stream.read(1)
    return char == '\n'

def CarriageReturn(stream):
    """
    This function can be passed as value for the *newline* argument
    of the :class:`Scanner` constructor to handle only carriage-return
    characters as newlines. It is usually recommended to use the
    carriage-return character as *newline_char* for the Scanner when
    using this newline handler.
    """

    char = stream.read(1)
    return char == '\r'

class Scanner(object):
    """
    The Scanner is a useful class for processing text as a stream
    of characters. It can handle universal and even customized
    newlines and will return a linefeed for it.

    :param stream: A stream of characters. Basically, this is a
        subset of the file-object interface, but only the `read()`,
        `tell()` and `seek()` methods are required.
    :param newline: A function that accepts the *stream* as
        sole argument and returns True if a newline was detected
        from that position. The default argument is :func:`Universal`.
    :param newline_char: The character that will represent a newline
        detected by the *newline* handler. It is usually recommended
        to use a character that appears in the newline sequence
        matched by the handler.
    """

    def __init__(self, stream, newline=Universal, newline_char='\n'):
        super(Scanner, self).__init__()
        self.stream = stream
        self.newline = newline
        self.newline_char = newline_char
        self.position = stream.tell()
        self.column = 0
        self.line = 1
        self.char = None

        if not callable(newline):
            raise TypeError('`newline` must be callable')

    def __repr__(self):
        text = '<Scanner at line {0}, column {1}>'
        return text.format(self.line, self.column)

    def __iter__(self):
        """
        Returns a generator that iterates over every line of the
        stream as extraced by :meth:`getline` and yields tuples of
        ``(cursor, line)``.

        :raise RuntimeError: see :meth:`getline`
        """

        cursor, line = self.cursor(), self.getline()
        while line:
            yield cursor, line
            cursor, line = self.cursor(), self.getline()

    def next(self):
        """
        Reads the next character from the scanner and returns it.
        Returns an empty string if the end of the stream was reached.
        """

        # If the current character is not None but an empty
        # object (we don't want to assume an empty string),
        # the stream is at its end already.
        char = self.char
        if char is not None and not char:
            return char

        # Let the newline handler check if there is a newline
        # at the current position of the stream.
        stream = self.stream
        pos = stream.tell()
        if self.newline(stream):
            self.position = stream.tell()
            self.line += 1
            self.column = 0
            char = self.newline_char

        # If it is not, we'll simply read in a character.
        else:
            self.stream.seek(pos)
            self.position = pos + 1
            self.column += 1
            char = stream.read(1)

        self.char = char
        return char

    def cursor(self):
        """
        Returns a tuple of ``(position, line, column)`` that
        represents the Scanners current position in the stream.
        Can be used with :meth:`seek` to re-position the Scanner.
        """

        return (self.position, self.line, self.column)

    def seek(self, cursor):
        """
        Re-positions the Scanner at the specified cursor location.
        The *cursor* value should have previously been obtained with
        :meth:`cursor` to not mess with the line and column numbers.
        """

        position, line, column = cursor

        if position < 0:
            raise ValueError('can\'t seek to negative position')
        elif position == 0:
            self.stream.seek(0)
            self.char = None
        else:
            self.stream.seek(position - 1)
            self.char = self.stream.read(1)

        self.position, self.line, self.column = position, line, column

    def consume(self, consumer):
        """
        Consume characters until the *consumer* function returns
        False. The function must accept two arguments, where the
        first is the current character of the Scanner and the
        second is the index of the character since the consuming
        started.

        If the *consumer* returns True for a character/index pair,
        the Scanner will head on to the next character. The consumed
        character sequence is returned as a string.

        :param consumer: The consumer function.
        :raise RuntimeError: If the Scanner has not touched the
            input stream before this function was called. You can
            touch the stream by calling :meth:`next` to read the
            first character.
        """

        char = self.char
        if char is None:
            raise RuntimeError(
              'Scanner.next() must be called at least once before consuming')

        result = ''
        while char and consumer(char, len(result)):
            result += char
            char = self.next()
        return result

    def getline(self):
        """
        Consumes all characters until a newline character was
        found and returns a string of the consumed sequence.
        The returned string will include the newline character
        if not the end of the stream was reached.

        :raise RuntimeError: If the Scanner has not touched the
            input stream before this function was called. You can
            touch the stream by calling :meth:`next` to read the
            first character.
        """

        char = self.char
        if char is None:
            raise RuntimeError(
              'Scanner.next() must be called at least once before consuming')

        got_newline = False
        newline_char = self.newline_char

        result = ''
        while char and not got_newline:
            result += char
            got_newline = (char == newline_char)
            char = self.next()

        return result

