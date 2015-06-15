"""``base`` module of ``dataql.parsers``.

It provides the base parser each subclass should inherit from, and the metaclass used
to manage the creation of the grammar using the ones from all parent classes.

"""

from inspect import isfunction
import re

from parsimonious import Grammar, NodeVisitor, rule
from parsimonious.nodes import RuleDecoratorMeta as BaseRuleDecoratorMeta

from dataql.resources import *


class RuleDecoratorMeta(BaseRuleDecoratorMeta):
    """Metaclass to use the @rule decorator.

    This metaclass allows to convert @rule decorators into real rules, but also to inherit
    from grammar defined in parent classes, allowing to override some rules.

    Notes
    -----

    This is a rewrite of the decorator provided by ``parsimonious``, to better handle
    inheritance (but adding up the grammar of all parents, using the fact that last defined
    rule with the same name is the one to use).
    It also handles the case when we want a rule to be just another one, for example ``OPER`` to
    be ``COL_OR_EQ``. This is not well handled by parsimonious, so we catch this kind of rule and
    add " NOOP" at the end to trick parsimonious.
    We also split ourselves the rules into key/values because parsimonious cannot correctly handle
    raw regular expressions.

    """

    # Regex to split rules in key/value parts.
    grammar_simple_parser = re.compile(r'^\s*([a-zA-Z_][a-zA-Z_0-9]*)\s+=')
    # Regex to detect rules that are just a synonym to another one composed of only an identifier.
    ident_simple_parser = re.compile(r'^\s*([a-zA-Z_][a-zA-Z_0-9]*)(\s*(?:#.*)?)$')

    def __new__(mcs, name, bases, namespace):

        def get_rule_name_from_method(method_name):
            """Remove any leading "visit_" from a method method_name."""
            return method_name[6:] if method_name.startswith('visit_') else method_name

        # Grammar starts by the full grammar from parents (each parent can redefine a part).
        grammar_parts = [getattr(b, 'grammar_str', '') for b in reversed(bases)]
        # Then add the base grammar defined in the current class.
        grammar_parts.append(namespace.get('base_grammar', ''))

        # Get all methods to use as rules (the ones decorated by ``@rule``).
        methods = [v for k, v in namespace.items() if
                   hasattr(v, '_rule') and isfunction(v)]

        if methods:
            # Keep them in the order defined in the code source.
            methods.sort(key=lambda x: x.__code__.co_firstlineno)

            for method in methods:
                method_rule = method._rule
                # Manage aliases: parsimonious cannot manage rules like "KEY = OTHERKEY"
                # So we add a no-op.
                match = mcs.ident_simple_parser.match(method_rule)
                if match:
                    method_rule = '%s NOOP %s' % match.groups()

                # Add the rule for this method in our grammar.
                grammar_parts.append('%s = %s' % (get_rule_name_from_method(method.__name__),
                                                  method_rule))

        # Make one big grammar string.
        grammar_str = '\n'.join(grammar_parts)

        # And ask parsimonious to convert it in a real ``Grammar`` object.
        namespace['grammar'] = Grammar(grammar_str)

        # Get the ``default_rule`` defined in our class, or find one from parents.
        default_rule = namespace.get('default_rule')
        if not default_rule:
            for base in bases:
                default_rule = getattr(base, 'default_rule', '')
                if default_rule:
                    break

        if default_rule:
            # Defining a default rule change the Grammar (immutable, so we get a new one).
            namespace['grammar'] = namespace['grammar'].default(default_rule)

        # Recreate the whole ``grammar_str`` to be inherited by future subclasses.
        # We cannot rely on str(namespace['grammar']) because r'' strings are not managed correctly
        grammar_dict = {}
        for line in grammar_str.split('\n'):
            match = mcs.grammar_simple_parser.match(line)
            if match:
                grammar_dict[match.group(1)] = line.strip()
        namespace['grammar_str'] = '\n'.join(grammar_dict.values())

        # We don't want to exec the __new__ method of our super class, ie BaseRuleDecoratorMeta
        # because we just rewrite everything it does.
        return super(BaseRuleDecoratorMeta,
                     mcs).__new__(mcs, name, bases, namespace)


class BaseParser(NodeVisitor, metaclass=RuleDecoratorMeta):
    """Base for all parsers in the ``dataql`` library. Defined default simple rules.


    This base parser defines the following simple rules that can be used in subclasses:

        - WS          => White space
        - NOOP        => No-op: rule that match nothing.
        - PAR_O       => Open parenthesis (maybe surrounded by spaces)
        - PAR_C       => Closed parenthesis (maybe surrounded by spaces)
        - CUR_O       => Open curly bracket (maybe surrounded by spaces)
        - CUR_C       => Closed curly bracket (maybe surrounded by spaces)
        - BRA_O       => Open (square) bracket (maybe surrounded by spaces)
        - BRA_C       => Closed (square) bracket (maybe surrounded by spaces)
        - DOT         => A simple dot (maybe surrounded by spaces)
        - COM         => A simple comma (maybe surrounded by spaces)
        - COL         => A simple colon
        - EQ          => The equal sign
        - COL_OR_EQ   => Rule to assume that colon and equal sign are synonyms
        - IDENT       => An identifier (a valid python one)
        - OPER        => An operator (currently only "=" or ":")
        - VALUE       => A value (string, number, null, false or true)
        - STR         => A string
        - NB          => A number (int, float, with or without scientific notation)
        - NULL        => A ``None`` identifier ("null", "nil", "none", case insensitive)
        - FALSE       => A ``False`` identifier ("false" case insensitive)
        - TRUE        => A ``True`` identifier ("true" case insensitive)

    This base parser also provides a ``__init__`` methods that will take some text and parse it
    automatically, storing the resulting resource in the ``data`` attribute.

    Attributes
    ----------
    base_grammar : str
        Simple rules that don't need any function.
    grammar : Grammar
        Instance of the ``parsimonious.Grammar`` class that holds the compiled grammar.
    grammar_str : str
        String representation of the ``grammar`.
    Field : class
        The class to use as a ``Field`` resource. Default to ``dataql.resources.Field``.
    Object : class
        The class to use as a ``Object`` resource. Default to ``dataql.resources.Object``.
    List : class
        The class to use as a ``List`` resource. Default to ``dataql.resources.List``.
    Filter : class
        The class to use as a ``Filter``. Default to ``dataql.resources.Filter``.
    NamedArg : class
        The class to use as a ``NamedArg`` (named argument). Default to
        ``dataql.resources.NamedArg``.
    PosArg : class
        The class to use as a ``PosArg`` (positioned argument). Default to
        ``dataql.resources.PosArg``.


    Notes
    -----

    Resources
    `````````

    Parsers use resources defined in ``dataql.resources`` to convert a query in usable structure.
    All classes are set as attributes of the parser. It allows to defined a new resource class,
    and override a parser to simply change the way a resource is used.

    About inheritance
    `````````````````

    Each subclass grammar is composed from all its parents ``grammar_str`` values, then its own
    ``base_grammar`, then the rules defined by the ``@rule`` decorators (in the order defined in
    the source code).
    If many rules share the same name, the last defined one, in the order defined in the above
    sentence, is the one that will be used, the others ignored. It allows to easily override a rule.

    """

    base_grammar = r"""
        WS     =  ~"\s*"
        NOOP = ""

        PAR_O  =  WS "(" WS
        PAR_C  =  WS ")" WS
        CUR_O  =  WS "{" WS
        CUR_C  =  WS "}" WS
        BRA_O  =  WS "[" WS
        BRA_C  =  WS "]" WS

        DOT = WS "." WS
        COM = WS "," WS

        COL = ":"
        EQ = "="
        COL_OR_EQ = COL / EQ

    """

    Field = Field
    List = List
    Object = Object
    Filter = Filter
    NamedArg = NamedArg
    PosArg = PosArg

    def __init__(self, text, default_rule=None):
        """Init the parser with some text to parse, and parse it.

        The resource resulting in the parsing will be stored in the ``data`` attribute.

        Arguments
        ---------
        text : str
            The text to parse.
        default_rule : str, optional
            A default rule to use to override the default one.

        Example
        -------

        >>> parser = BaseParser('foo', default_rule='IDENT')
        >>> parser.data
        'foo'

        """

        # If we want another default rule, it will create a new grammar object.
        if default_rule:
            self.grammar = self.grammar.default(default_rule)

        # Parse the text and save the resource in the ``data`` attribute.
        self.data = self.parse(text)

    def generic_visit(self, node, children):
        """Methods called for all rules with specific methods. Does nothing."""
        pass

    @rule('~"[_A-Z][_A-Z0-9]*"i')
    def visit_IDENT(self, node, children):
        """Return a valid python identifier.

        It may be used for a resource name, a filter...

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list, unused

        Result
        ------
        str
            The identifier as string.


        Example
        -------

        >>> BaseParser('foo', default_rule='IDENT').data
        'foo'
        >>> BaseParser('_foo', default_rule='IDENT').data
        '_foo'
        >>> BaseParser('fooBar', default_rule='IDENT').data
        'fooBar'
        >>> BaseParser('foo_Bar', default_rule='IDENT').data
        'foo_Bar'
        >>> BaseParser('foo1', default_rule='IDENT').data
        'foo1'
        >>> BaseParser('1foo', default_rule='IDENT').data # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        parsimonious.exceptions.ParseError:
        >>> BaseParser('foo-bar', default_rule='IDENT').data # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        parsimonious.exceptions.IncompleteParseError:

        """

        return node.text

    @rule('COL_OR_EQ')
    def visit_OPER(self, node, children):
        """Return an operator as a string. Currently only "=" and ":" (both synonyms)

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list, unused

        Result
        ------
        str
            The operator as a string.

        Example
        -------

        >>> BaseParser('=', default_rule='OPER').data
        '='
        >>> BaseParser(':', default_rule='OPER').data
        '='

        """

        oper = node.text
        if oper == ':':
            oper = '='
        return oper

    @rule('STR / NB / NULL / FALSE / TRUE')
    def visit_VALUE(self, node, children):
        """Return a value, which is a string, a number, a null/false/true like value.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: the value to return

        Result
        ------
        str or int or float or None or False or True

        Example
        -------

        >>> BaseParser('"foo"', default_rule='VALUE').data
        'foo'
        >>> BaseParser('1', default_rule='VALUE').data
        1
        >>> BaseParser('0.1', default_rule='VALUE').data
        0.1
        >>> BaseParser('null', default_rule='VALUE').data is None
        True
        >>> BaseParser('false', default_rule='VALUE').data
        False
        >>> BaseParser('true', default_rule='VALUE').data
        True

        """

        return children[0]

    @rule(r'~"([\'\"])(?:[^\\1\\\\]|\\\\.)*?\\1"')
    def visit_STR(self, node, children):
        """Regex rule for quoted string allowing escaped quotes inside.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list, unused

        Result
        ------
        str
            The wanted string, with quoted characters unquoted.

        Example
        -------

        >>> BaseParser('"foo"', default_rule='STR').data
        'foo'
        >>> BaseParser("'foo'", default_rule='STR').data
        'foo'
        >>> BaseParser('''"foo b'ar"''', default_rule='STR').data
        "foo b'ar"
        >>> BaseParser('''"foo b\'ar"''', default_rule='STR').data
        "foo b'ar"
        >>> BaseParser(r"'foo b\\'ar'", default_rule='STR').data
        "foo b'ar"

        Notes
        -----

        The regex works this way:
            Two quotes (single or double, the starting one and the ending one should be the same)
            surrounding zero or more of "any character that's not a quote (same as the
            starting/ending ones) or a backslash" or "a backslash followed by any character".

        """

        # remove surrounding quotes and remove single backslashes
        return self.visit_STR.re_single_backslash.sub('', node.text[1:-1])
    # regex  to unquote single quote characters
    visit_STR.re_single_backslash = re.compile(r'(?<!\\)\\')

    @rule('~"[-+]?\d*\.?\d+([eE][-+]?\d+)?"')
    def visit_NB(self, node, children):
        """Return a int of float from the given number.

        Also work with scientific notation like 1e+50.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list, unused

        Result
        ------
        int or float

        Example
        -------

        >>> BaseParser('1', default_rule='NB').data
        1
        >>> BaseParser('-3', default_rule='NB').data
        -3
        >>> BaseParser('0', default_rule='NB').data
        0
        >>> BaseParser('0.0', default_rule='NB').data
        0.0
        >>> BaseParser('1.0', default_rule='NB').data
        1.0
        >>> BaseParser('9999999999', default_rule='NB').data
        9999999999
        >>> BaseParser('1e+50', default_rule='NB').data
        1e+50
        >>> BaseParser('-2.5e33', default_rule='NB').data
        -2.5e+33

        """

        return self.convert_nb(node.text)

    @rule('~"(?:null|nil|none)"i')
    def visit_NULL(self, node, children):
        """Return ``None`` for the string "null", "none", or "nil" (case insensitive)

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list, unused

        Returns
        -------
        None

        Example
        -------

        >>> BaseParser('null', default_rule='NULL').data is None
        True
        >>> BaseParser('Null', default_rule='NULL').data is None
        True
        >>> BaseParser('NULL', default_rule='NULL').data is None
        True
        >>> BaseParser('nil', default_rule='NULL').data is None
        True
        >>> BaseParser('Nil', default_rule='NULL').data is None
        True
        >>> BaseParser('NIL', default_rule='NULL').data is None
        True
        >>> BaseParser('none', default_rule='NULL').data is None
        True
        >>> BaseParser('None', default_rule='NULL').data is None
        True
        >>> BaseParser('NONE', default_rule='NULL').data is None
        True

        """

        return None

    @rule('~"(?:false)"i')
    def visit_FALSE(self, node, children):
        """Return ``False`` for the string "false" (case insensitive)

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list, unused

        Returns
        -------
        False

        Example
        -------

        >>> BaseParser('false', default_rule='FALSE').data
        False
        >>> BaseParser('False', default_rule='FALSE').data
        False
        >>> BaseParser('FALSE', default_rule='FALSE').data
        False

        """

        return False

    @rule('~"(?:true)"i')
    def visit_TRUE(self, node, children):
        """Return ``True`` for the string "true" (case insensitive)

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list, unused

        Returns
        -------
        True

        Example
        -------

        >>> BaseParser('true', default_rule='TRUE').data
        True
        >>> BaseParser('True', default_rule='TRUE').data
        True
        >>> BaseParser('TRUE', default_rule='TRUE').data
        True

        """

        return True

    @staticmethod
    def convert_nb(text):
        """Tries to convert the given the given text as a number.

        Also work with scientific notation like 1e+50.

        Arguments
        ---------
        text : string
            The text to convert.

        Result
        ------
        int or float

        Example
        -------

        >>> BaseParser('').convert_nb('1')
        1
        >>> BaseParser('').convert_nb('-3')
        -3
        >>> BaseParser('').convert_nb('0')
        0
        >>> BaseParser('').convert_nb('0.0')
        0.0
        >>> BaseParser('').convert_nb('1.0')
        1.0
        >>> BaseParser('').convert_nb('9999999999')
        9999999999
        >>> BaseParser('').convert_nb('1e+50')
        1e+50
        >>> BaseParser('').convert_nb('-2.5e33')
        -2.5e+33

        """

        try:
            return int(text)
        except ValueError:
            return float(text)
