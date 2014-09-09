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

import collections

__all__ = ['Str', 'Set']

class Matcher(object):
    """ Interface for matchers. Matchers are callable objects that
    accept a :class:`strex.scan.Scanner` as the sole argument and
    return either None or a non-empty string. """

    def __call__(self, scanner):
        raise NotImplementedError

class Str(Matcher):
    """ Implements matching an exact string (or character
    sequence) from the current position of a :class:`Scanner`.
    Optionally, the matching can be case-insensitive.

    :param sequence: A sequence of characters.
    :param ignore_case: If True, the string will be
        matched case-insensitive.
    """

    def __init__(self, sequence, ignore_case=False):
        super(Str, self).__init__()
        self.sequence = ''.join(sequence)
        self.ignore_case = bool(ignore_case)
        if self.ignore_case:
            self.sequence = self.sequence.lower()

    def __repr__(self):
        return 'Str({!r})'.format(self.sequence)

    def __call__(self, scanner):
        result = collections.deque()
        for char in self.sequence:
            other = scanner.char
            if not other or char != other:
                return None
            result.append(other)
            scanner.next()
        return ''.join(result)

class Set(Matcher):
    """ Implements matching a set. The arguments to constructing
    an instance of this class are similar to the arguments of
    :meth:`strex.scan.Scanner.read_set`.
    """

    def __init__(self, charset, max=-1, inverted=False, ignore_case=False):
        super(Set, self).__init__()
        charset = ''.join(charset)
        if ignore_case:
            charset = charset.lower()

        self.charset = frozenset(charset)
        self.max = int(max)
        self.inverted = bool(inverted)
        self.ignore_case = bool(ignore_case)

    def __repr__(self):
        return 'Set({!r})'.format(''.join(self.charset))

    def __call__(self, scanner):
        result = scanner.read_set(self.charset, self.max, self.inverted,
                lowercase=self.ignore_case)
        if not result:
            result = None
        return result

