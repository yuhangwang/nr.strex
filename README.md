*nr.strex* - Python string processing
=====================================

String Extensions is a package for Python 2 & 3 for processing text and
character streams in an easy fashion. It makes parsing of minilanguages
or even complete text file formats easy.

## Example

### Tokenization

```python
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
```

----------------------------------------------------------------------

Copyright (C) 2013-2015 Niklas Rosenstein. Licensed under the MIT license.
