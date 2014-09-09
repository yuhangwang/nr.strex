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
"""
The contents of this module enable easy development of
cross-Python version code.
"""

import sys
PY3 = sys.version_info[0] >= 3
PY2 = not PY3

if PY2:
    try: from cStringIO import StringIO
    except ImportError: from StringIO import StringIO

    from itertools import izip as zip
    range = xrange
    input = raw_input

    def print_(*args, **kwargs):
        sep = str(kwargs.pop('sep', ' '))
        end = str(kwargs.pop('end', '\n'))
        file = str(kwargs.pop('file', sys.stdout))

        for arg in args[:-1]:
            file.write(str(arg))
            file.write(sep)
        if args:
            file.write(str(args[-1]))
        file.write(end)

    string_types = (basestring,)
    text_type = unicode

else:
    from io import StringIO

    zip = zip
    range = range
    input = input

    print_ = __builtins__['print']

    string_types = (bytes, str)
    text_type = str
