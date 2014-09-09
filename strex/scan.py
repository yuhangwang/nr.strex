# Copyright (c) 2014  Niklas Rosenstein
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

from .six import StringIO, string_types
import collections

__all__ = ['Scanner']

class Scanner(object):
    """ The *Scanner* class is used for processing an input stream
    of unicode characters while counting line- and column-numbers.
    It exposes many convenience methods for easily processing the
    stream.

    A *Scanner* instance contains a buffer of the read characters
    for which the size must be specified upon initialization. Within
    this buffer, seeking is supported. Some methods that read from
    the input stream can fail if the buffer size was chosen too
    little.

    :param fp: An file-like object serving as the input stream.
    :param bufsize: The size of the buffer that will contain the
        characters that have already been read from *fp*.
    """

    # This object is used to represent the start in case the
    # Scanner seeks to the beginning of the input stream.
    start = type('start_type', (), {
        '__bool__': lambda s: False,
        '__repr__': lambda s: '<start>',
        })()

    # This object is used to mark the end of the input stream.
    end = type('end_type', (), {
        '__bool__': lambda s: False,
        '__repr__': lambda s: '<end>',
        })()

    def __init__(self, fp, bufsize=512):
        super(Scanner, self).__init__()
        self.fp = fp
        self.bufsize = bufsize + 1 # include Scanner.start
        self.buffer = collections.deque([Scanner.start])
        self.buffer_index = 0
        self.position = 0
        self.line = 1
        self.column = 0

    def _update_cursor(self):
        """ Updates the cursor information depending on the current
        character in the Scanner. Called from :meth:`next`.

        :internal: """

        if self.char == '\n':
            self.line += 1
            self.column = 0
        else:
            self.column += 1
        self.position += 1

    @property
    def char(self):
        """ The current character the :class:`Scanner` is pointing
        to in the input stream. This is :data:`Scanner.start`, a
        one-character string or :data:`Scanner.end`. """

        return self.buffer[self.buffer_index]

    def next(self):
        """ Returns the next character in the input stream. If
        the end of the input stream was reached, :data:`Scanner.end`
        is returned. After this method was called, the same value
        it returns will be returned by :attr:`char`. """

        # If the buffer_index is not pointing to the last item
        # in the buffer, we need to increment the buffer_index
        # by one as we are moving in the buffered content of
        # the inputn stream.
        if self.buffer_index < len(self.buffer) - 1:
            self.buffer_index += 1
            self._update_cursor()
            return self.char

        # If we are already pointing to the end of the input
        # stream, we're not gonna do anything else.
        if self.char == self.end:
            return self.end

        # Read the next character from the input stream. If
        # the end was reached, we convert it to the respective
        # representative.
        char = self.fp.read(1)
        if not char:
            char = self.end

        # We only want to cut the buffer to contain
        # no more than the specified number of elements.
        self.buffer.append(char)
        while len(self.buffer) > self.bufsize:
            self.buffer.popleft()

        self.buffer_index = len(self.buffer) - 1
        self._update_cursor()
        return self.char

    def get_cursor(self):
        """ Returns a tuple of ``(position, line, column)`` that
        can be used at a later point to restore the position of
        the Scanner. """

        return (self.position, self.line, self.column)

    def set_cursor(self, cursor):
        """ Moves the position of the :class:`Scanner` to the
        specified *position* and adapts the *line* and *column*
        numbers. A tuple that has previously been generated by
        :meth:`get_cursor` should be passed to this function.

        :raise RuntimeError: If the designated
            *position* is out of the buffers bounds. Seeking
            forward is also only supported within the buffers
            range.
        """

        # Unpack the cursor tuple.
        position, line, column = cursor

        # Calculate the offset and make sure it is within
        # the buffers range.
        delta = position - self.position
        if (delta + self.buffer_index) > len(self.buffer):
            raise RuntimeError("forward seek out of range")
        elif (delta + self.buffer_index) < 0:
            raise RuntimeError("backward seek out of range")

        self.buffer_index += delta
        self.position = position
        self.line = line
        self.column = column

    cursor = property(get_cursor, set_cursor)

    def read_set(self, charset, max=-1, inverted=False, lowercase=False):
        """ Reads all characters from the current position that
        are contained in *charset* and concatenates them into a
        single string. If *max* is a positive number, no more
        than this number of characters will be read. Passing
        *True* for *inverted* will invert the *charset*.

        :param charset: A collection of characters that should
            be accepted (or rejected if *inverted* is True) for
            the resulting string.
        :param max: The maximum number of characters to read
            from the input stream.
        :param inverted: If this parameter is passed *True*,
            the *charset* defines what characters to reject
            instead of to accept for the resulting string.
        :param lowercase: If this parameter is *True*, the
            characters read from the input stream will be
            converted to lowercase before checking them against
            the *charset*.
        """

        result = collections.deque()
        while True:
            char = self.char
            if not char: break
            if max >= 0 and len(result) >= max: break
            if lowercase: char = char.lower()
            if inverted and char in charset: break
            elif not inverted and char not in charset: break
            result.append(char)
            self.next()
        return ''.join(result)

    def skip_set(self, charset, max=-1, inverted=False, lowercase=False):
        """ Like :meth:`read_set`, but returns the number of characters
        that have been read. """

        return len(self.read_set(charset, max, inverted, lowercase))

    def match(self, matcher, fallback=False):
        """ Applies a matcher object to the Scanner which is basically
        just a callable object that accepts a single argument, the
        scanner itself. If the matcher returns not None, but a string
        or byte sequence, the matching is considered successful. If the
        matching was not successful or *fallback* is set to True, the
        scanner will be re-set to its original position in the buffered
        input stream. """

        cursor = self.cursor
        result = matcher(self)
        if result is None or fallback:
            self.cursor = cursor
        if not isinstance(result, string_types):
            raise RuntimeError('matcher returned not None or string type')
        return result

    @staticmethod
    def from_string(string, bufsize=512):
        """ Creates a new :class:`Scanner` from a string. If
        *None* is passed for *bufsize*, the length of the string
        will be used as the potential buffer size. """

        if len(string) < bufsize:
            bufsize = len(string) + 1
        return Scanner(StringIO(string), bufsize)

