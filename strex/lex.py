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

from . import scan, match
import string
import collections

__all__ = ['Lexicon', 'SyntaxNode', 'Ref', 'All', 'Either', 'Str', 'Set']


class SyntaxNode(object):
    """ This class represents a node in an abstract syntax
    tree. Each node has a cursor position from which it was
    extracted from the input stream, a type ID (which can be
    anything but is usually a string) and a value. The value
    of a node may be an empty string.

    :param value: A string
    :param type: Any object
    :param cursor: A 3-integer tuple *(position, line, column)*

    .. attribute:: value

    .. attribute:: type

    .. attribute:: cursor

    .. attribute:: children
    """

    def __init__(self, value, type, cursor):
        super(SyntaxNode, self).__init__()
        self.value = value
        self.type = type
        self.cursor = cursor
        self.children = []

    def __repr__(self):
        message = '<SyntaxNode#{!s}: {!r} @ {!s}>'
        return message.format(self.type, self.value, self.cursor)

class Lexicon(object):
    """ This class represents the syntax declarations.

    :param collapse_tree: If this is set to True, SyntaxNodes
        with their :attr:`type<SyntaxNode.type>` attribute set
        to None and have one or no child nodes will be collapsed.
    """

    def __init__(self, reduce_mode='normal'):
        super(Lexicon, self).__init__()
        self.reduce_mode = reduce_mode
        self._wslist = []
        self._wsdict = {}
        self._rulelist = []
        self._ruledict = {}
        self._skip_whitespace_invoked = False

    def __setitem__(self, name, extractors, ws_rule=False, ws_reduce=True):
        # If not a list or tuple was passed, we assume that
        # the intention was to pass a list with only one item.
        if not isinstance(extractors, (list, tuple)):
            extractors = [extractors]
        extractors = process_extractor_list(extractors)

        if not extractors:
            raise ValueError('need at least one Extractor for a rule')
        elif len(extractors) == 1:
            ex = extractors[0]
        else:
            ex = All(*extractors)

        if ws_rule:
            self._wsdict[name] = (ex, ws_reduce)
            self._wslist.append([name, ex, ws_reduce])
        else:
            self._ruledict[name] = ex
            self._rulelist.append([name, ex])

    def __getitem__(self, name):
        """ Returns a :class:`Extractor` object that was
        registered as a rule to the Lexicon under the
        specified name.

        :raise KeyError: If *name* is not a registered rule.
        """

        return self._ruledict[name]

    def whitespace_rule(self, name, extractors, reduce=True):
        """ Adds a whitespace rule which is being invoked from
        an Extractor before it tries to match with
        :meth:`skip_whitespace`. If *reduce* is set to True,
        the extracted nodes whitespace nodes won't be included
        in the tree. """

        self.__setitem__(name, extractors, ws_rule=True, ws_reduce=reduce)

    @property
    def reduce_mode(self):
        return self._reduce_mode

    @reduce_mode.setter
    def reduce_mode(self, mode):
        if mode not in ('noreduce', 'normal', 'tight'):
            raise ValueError('reduce_mode must be none, normal or tight')
        self._reduce_mode = mode

    def skip_whitespace(self, scanner):
        """ Skips whitespace characters and returns a list of
        :class:`SyntaxNode`s that contains the non-reduced whitespace
        tokens. """

        if self._skip_whitespace_invoked:
            return []
        self._skip_whitespace_invoked = True
        try:
            nodes = []
            while True:
                # Match all whitespace rules until no rule matched.
                matched = False
                for name, ex, reduce_ in self._wslist:
                    nodelist = ex.extract(self, scanner, name)
                    if nodelist:
                        matched = True
                        if not reduce_:
                            nodes.extend(nodelist)

                if not matched:
                    break
        finally:
            self._skip_whitespace_invoked = False

        return nodes

    def parse(self, scanner):
        """ Applies all registered rules (in the specified order)
        to the given :class:`scan.Scanner` instance and returns a
        :class:`SyntaxNode` or None. """

        for name, ex in self._rulelist:
            cursor = scanner.cursor
            nodelist = ex.extract(self, scanner, name)
            if nodelist:
                final = []
                for node in nodelist:
                    if self._reduce_mode == 'normal':
                        node = collapse_tree(node, tight=False)
                    elif self._reduce_mode == 'tight':
                        node = collapse_tree(node, tight=True)
                    elif self._reduce_mode != 'noreduce':
                        msg = 'invalid reduce mode {0!r}'
                        raise RuntimeError(msg.format(self._reduce_mode))
                    final.append(node)
                return final
            scanner.cursor = cursor

        return None


class Extractor(object):
    """ This class represents an Extractor that is capable
    of extracting a syntax-node from a :class:`Scanner`. """

    def __init__(self, name=None):
        super(Extractor, self).__init__()
        self.name = name

    def create_node(self, value, rule, cursor):
        """ This method must be used for creating a
        :class:`SyntaxNode` instead of creating an instance
        directly. It will call :meth:`Lexicon.node_extracted`
        and default to :attr:`name` if *rule* is None. """

        return SyntaxNode(value, rule or self.name, cursor)

    def extract(self, lexicon, scanner, rule):
        """ Extract a token from the *scanner* and return
        a list of :class:`SyntaxNode` objects. Return an
        empty list if the Extractor does not match.

        *rule* is the name of the rule that was directly
        associated with this Extractor. When invoking
        sub-extractors that are not a rule by themselves,
        this parameter should be set to None instead.

        If *rule* is not set to None, the Extractor
        should use it for :attr:`SyntaxNode.type` if it
        has no other better suting type ID. """

        raise NotImplementedError

class MatcherExtractor(Extractor):
    """ This class wraps a :class:`match.Matcher` implementation
    instance or callable object. """

    def __init__(self, callable, **kwargs):
        super(MatcherExtractor, self).__init__(**kwargs)
        self.callable = callable

    def __repr__(self):
        return str(self.callable)

    def extract(self, lexicon, scanner, rule):
        nodes = lexicon.skip_whitespace(scanner)

        cursor = scanner.cursor
        result = self.callable(scanner)
        if not result:
            return None

        if not isinstance(result, str):
            clsname = result.__class__.__name__
            message = '{0}() returned {1}, expected str'
            message = message.format(self.callable.__name__, clsname)
            raise TypeError(message)

        nodes.append(self.create_node(result, rule, cursor))
        return nodes

    @staticmethod
    def factorize(matcher):
        """ Returns a callable object that creates a new
        :class:`MatcherExtractor` with the specified matcher.
        The *name* argument will be popped from the keyword
        arguments to the matcher.

        *matcher* must be a :class:`Matcher` subclass, not an
        instance. """

        if not issubclass(matcher, match.Matcher):
            raise ValueError('expected Matcher subclass')

        def factory(*args, **kwargs):
            exkwargs = {}
            if 'name' in kwargs:
                exkwargs['name'] = kwargs.pop('name')
            return MatcherExtractor(matcher(*args, **kwargs), **exkwargs)

        factory.__name__ = matcher.__name__
        return factory

class Ref(Extractor):
    """ This class cross-references a :class:`Lexicon` rule
    by name. """

    def __init__(self, rule_name, **kwargs):
        super(Ref, self).__init__(**kwargs)
        self.rule_name = rule_name

    def __repr__(self):
        return 'Ref({!r})'.format(self.rule_name)

    def extract(self, lexicon, scanner, rule):
        rule = lexicon[self.rule_name]
        return rule.extract(lexicon, scanner, self.rule_name)

class All(Extractor):
    """ This :class:`Extractor` implementation matches all
    specified sub Extractors sequentially. """

    def __init__(self, *extractors, **kwargs):
        super(All, self).__init__(**kwargs)
        self.extractors = process_extractor_list(extractors)

    def __repr__(self):
        return 'All(' + ', '.join(str(ex) for ex in self.extractors) + ')'

    def extract(self, lexicon, scanner, rule):
        node = self.create_node('', rule, scanner.cursor)
        for ex in self.extractors:
            nodelist = ex.extract(lexicon, scanner, None)
            if not nodelist:
                return []
            node.children.extend(nodelist)
        return [node]

class Either(Extractor):
    """ This :class:`Extractor` implementation stops at the
    first sub Extractor matching the current Scanner. """

    def __init__(self, *extractors, **kwargs):
        super(Either, self).__init__(**kwargs)
        self.extractors = process_extractor_list(extractors)

    def __repr__(self):
        return 'Either(' + ', '.join(str(ex) for ex in self.extractors) + ')'

    def extract(self, lexicon, scanner, rule):
        cursor = scanner.cursor
        node = self.create_node('', rule, cursor)
        for ex in self.extractors:
            nodelist = ex.extract(lexicon, scanner, None)
            if nodelist:
                node.children.extend(nodelist)
                return [node]
            scanner.cursor = cursor
        return []

Str = MatcherExtractor.factorize(match.Str)
Set = MatcherExtractor.factorize(match.Set)


def collapse_tree(node, tight=False):
    """ Given a :class:`SyntaxNode`, this function will return
    a modified hierarchical structure, collapsing all nodes that
    have their :attr:`SyntaxNode.type` attribute set to None and
    have :attr:`SyntaxNode.collapse` set to True AND have only
    one child node.

    If *tight* is set to True, every node that has no value and
    one or no children will be collapsed, not respecting when a
    node has a type specified.

    If *tight* is set to False, the type of a node is taken into
    account, but nodes with multiple children may be collapsed as
    well. """

    index = 0
    while index < len(node.children):
        child = collapse_tree(node.children[index], tight)

        # Check if this child-node can be collapsed.
        collapsible = not child.value and len(child.children) <= 1
        if not tight:
            collapsible &= not child.type

        # If it is collapsible, we will remove it from the
        # child-list of the parent node. If this child has
        # another child node, it will be replace this child.
        if collapsible:
            del node.children[index]
            for new_child in child.children:
                node.children.insert(index, new_child)
                index += 1
            index -= 1
        index += 1

    if len(node.children) == 1:
        child = node.children[0]
        if not child.type and not child.value:
            node.children[:] = child.children

    return node

def process_extractor_list(extractors):
    """ Processes the list *extractors* and returns a new
    list that is garuanteed to contain :class:`Extractor`
    instances only, or raise a :class:`TypeError`.

    *extractors* may contain :class:`Extractor` instances,
    :class:`match.Matcher` instances, callables and strings. """

    # Validate the items in the *extractors* list by
    # automatically converting Matchers and strings.
    new_extractors = []
    for ex in extractors:
        # A string will be converted to a case-sensitive
        # Str matcher.
        if isinstance(ex, str):
            ex = Str(ex)

        # If not an Extractor was given, it must be a
        # callable that can be wrapped in a MatcherExtractor.
        if not isinstance(ex, Extractor):
            if not callable(ex):
                raise TypeError('expected Extractor, callable or string')

            ex = MatcherExtractor(ex)
        new_extractors.append(ex)

    return new_extractors


def traverse(node, callback, chain=None):
    """ This method traverses the hierarchy of a :class:`SyntaxNode`
    and invokes *callback* for each node. If *callback* returns a
    False value, the node is removed from its parents child-list.

    The callback must accept two arguments, the first being the
    current node and the second being a :class:`collections.deque`
    that contains the chain of parent nodes, with the closes parent
    being the last element.

    This method returns the *node* or None if the callback returned
    False on this node. """

    if chain is None:
        chain = collections.deque()

    if not callback(node, chain):
        if not chain:
            return None
        parent = chain[-1]
        parent.children.remove(node)
        return

    chain.append(node)
    for child in node.children:
        traverse(child, callback, chain)
    chain.pop()

    return node

def dumptree(node, file=None):
    def callback(node, chain):
        indent= '  ' * len(chain)
        type_ = (indent + '(%s)' % node.type).ljust(16)
        value = repr(node.value) if node.value else ''

        print('%s%s: %s' % (type_, indent, value))
        return True
    traverse(node, callback)


