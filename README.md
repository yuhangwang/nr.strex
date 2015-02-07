strex string processing
=======================

Strex is a utility package for processing strings and character
streams with ease. It is aimed specifically for developing
minilanguages.

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
