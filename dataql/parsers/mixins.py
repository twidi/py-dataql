"""``mixins`` module of ``dataql.parsers``.

It provides some mixin to ease the creation of complex parsers:
- NamedArgsParserMixin : manage named arguments
- UnnamedArgsParserMixin : manage unnamed arguments
- ArgsParserMixin : manage arguments (unnamed and named ones)
- FiltersParserMixin : manage filters (many successive filters, each filter is an identifier with
                       or without arguments)

"""

from dataql.parsers.base import BaseParser, rule


class NamedArgsParserMixin(BaseParser):
    """Parser mixin that provides rules to manage named arguments.

    A list of named arguments is a list of at least one named argument separated by a comma.
    An named argument is an identifier followed by an operator, followed by a value, ie a number,
    a string, or a null, false or true value.

    To use it, add this mixin to the class bases, and use ``NAMED_ARGS`` in your rule(s).

    Example
    -------

    >>> NamedArgsParserMixin(r'foo= 1').data
    [foo=1]
    >>> NamedArgsParserMixin(r'foo  = 1, bar="BAZ"').data
    [foo=1, bar="BAZ"]
    >>> NamedArgsParserMixin(r'foo=TRUE, bar ="BAZ",quz=null').data
    [foo=True, bar="BAZ", quz=None]

    >>> class TestParser(NamedArgsParserMixin, BaseParser):
    ...     default_rule = 'ROOT'
    ...     @rule('PAR_O NAMED_ARGS PAR_C')
    ...     def visit_ROOT(self, node, children):
    ...         return 'Content with named args: %s' % children[1]
    ...
    >>> TestParser('(foo=TRUE, bar ="BAZ",quz=null)').data
    'Content with named args: [foo=True, bar="BAZ", quz=None]'

    """

    default_rule = 'NAMED_ARGS'

    @rule('NAMED_ARG NEXT_NAMED_ARGS')
    def visit_NAMED_ARGS(self, node, children):
        """Named arguments of a filter.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: instance of ``.resources.NamedArg``, first named argument
            - 1: list of instances of ``.resources.NamedArg``, other named arguments

        Returns
        -------
        list(.resources.NamedArg)
            List of  instances of ``.resources.NamedArg``.

        Example
        -------

        >>> NamedArgsParserMixin(r'foo= 1', default_rule='NAMED_ARGS').data
        [foo=1]
        >>> NamedArgsParserMixin(r'foo  = 1, bar="BAZ"', default_rule='NAMED_ARGS').data
        [foo=1, bar="BAZ"]
        >>> NamedArgsParserMixin(r'foo=TRUE, bar ="BAZ",quz=null', default_rule='NAMED_ARGS').data
        [foo=True, bar="BAZ", quz=None]

        """

        return [children[0]] + (children[1] or [])

    @rule('COM NAMED_ARG')
    def visit_NEXT_NAMED_ARG(self, node, children):
        """Named argument of a filter following a previous one (so, preceded by a comma).

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: for ``COM`` (comma): ``None``.
            - 1: for ``NAMED_ARG``: instance of ``.resources.NamedArg``.

        Returns
        -------
        .resources.NamedArg
            Instance of ``.resources.NamedArg``.

        Example
        -------

        >>> NamedArgsParserMixin(r',foo= 1', default_rule='NEXT_NAMED_ARG').data
        foo=1
        >>> NamedArgsParserMixin(r' ,bar="BAZ"', default_rule='NEXT_NAMED_ARG').data
        bar="BAZ"
        >>> NamedArgsParserMixin(r', quz=null', default_rule='NEXT_NAMED_ARG').data
        quz=None
        >>> NamedArgsParserMixin(r', quz=TRUE', default_rule='NEXT_NAMED_ARG').data
        quz=True
        >>> NamedArgsParserMixin(r', quz=False', default_rule='NEXT_NAMED_ARG').data
        quz=False

        """

        return children[1]

    @rule('NEXT_NAMED_ARG*')
    def visit_NEXT_NAMED_ARGS(self, node, children):
        """Named arguments of a filter following the first one.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 1: list of instances of ``.resources.NamedArg``.

        Returns
        -------
        list(.resources.NamedArg)
            Instances of ``.resources.NamedArg``.

        Example
        -------

        >>> NamedArgsParserMixin(r'', default_rule='NEXT_NAMED_ARGS').data
        []
        >>> NamedArgsParserMixin(r',foo= 1', default_rule='NEXT_NAMED_ARGS').data
        [foo=1]
        >>> NamedArgsParserMixin(r' ,foo  : 1, bar="BAZ"', default_rule='NEXT_NAMED_ARGS').data
        [foo=1, bar="BAZ"]
        >>> NamedArgsParserMixin(r', foo=TRUE, bar ="BAZ",quz=null',
        ... default_rule='NEXT_NAMED_ARGS').data
        [foo=True, bar="BAZ", quz=None]

        """

        return children

    @rule('IDENT WS OPER WS VALUE')
    def visit_NAMED_ARG(self, node, children):
        """Named argument of a filter.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: name of the arg
            - 1: for ``WS`` (whitespace): ``None``.
            - 2: operator
            - 3: for ``WS`` (whitespace): ``None``.
            - 4: value of the named arg

        Returns
        -------
        .resources.NamedArg
            Instance of ``.resources.NamedArg``.

        Example
        -------

        >>> NamedArgsParserMixin(r'foo= 1', default_rule='NAMED_ARG').data
        foo=1
        >>> NamedArgsParserMixin(r'bar="BAZ"', default_rule='NAMED_ARG').data
        bar="BAZ"
        >>> NamedArgsParserMixin(r'quz=null', default_rule='NAMED_ARG').data
        quz=None
        >>> NamedArgsParserMixin(r'foo:TRUE', default_rule='NAMED_ARG').data
        foo=True
        >>> NamedArgsParserMixin(r'bar=False', default_rule='NAMED_ARG').data
        bar=False

        """

        return self.NamedArg(
            arg=children[0],
            arg_type=children[2],
            value=children[4],
        )


class UnnamedArgsParserMixin(BaseParser):
    """Parser mixin that provides rules to manage unnamed arguments.

    A list of unnamed arguments is a list of at least one unnamed argument separated by a comma.
    An unnamed argument is a value, ie a number, a string, or a null, false or true value.

    To use it, add this mixin to the class bases, and use ``UNNAMED_ARGS`` in your rule(s).

    Example
    -------

    >>> UnnamedArgsParserMixin(r'1').data
    [1]
    >>> UnnamedArgsParserMixin(r'1, 2').data
    [1, 2]
    >>> UnnamedArgsParserMixin(r'1,null, "foo"').data
    [1, None, "foo"]

    >>> class TestParser(UnnamedArgsParserMixin, BaseParser):
    ...     default_rule = 'ROOT'
    ...     @rule('PAR_O UNNAMED_ARGS PAR_C')
    ...     def visit_ROOT(self, node, children):
    ...         return 'Content with unnamed args: %s' % children[1]
    ...
    >>> TestParser('(1,null, "foo")').data
    'Content with unnamed args: [1, None, "foo"]'

    """

    default_rule = 'UNNAMED_ARGS'

    @rule('UNNAMED_ARG NEXT_UNNAMED_ARGS')
    def visit_UNNAMED_ARGS(self, node, children):
        """Unnamed arguments of a filter.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: instance of ``.resources.PosArg``, first unnamed argument
            - 1: list of instances of ``.resources.PosArg``, other unnamed arguments

        Returns
        -------
        list(.resources.NamedArg)
            List of  instances of ``.resources.PosArg``.

        Example
        -------

        >>> UnnamedArgsParserMixin(r'1', default_rule='UNNAMED_ARGS').data
        [1]
        >>> UnnamedArgsParserMixin(r'1, 2', default_rule='UNNAMED_ARGS').data
        [1, 2]
        >>> UnnamedArgsParserMixin(r'1,null, "foo"', default_rule='UNNAMED_ARGS').data
        [1, None, "foo"]

        """

        return [children[0]] + (children[1] or [])

    @rule('COM UNNAMED_ARG')
    def visit_NEXT_UNNAMED_ARG(self, node, children):
        """Unnamed argument of a filter following a previous one (so, preceded by a comma).

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: for ``COM`` (comma): ``None``.
            - 1: for ``UNNAMED_ARG``: instance of ``.resources.PosArg``.

        Returns
        -------
        .resources.PosArg
            Instance of ``.resources.PosArg``.

        Example
        -------

        >>> UnnamedArgsParserMixin(r', 1', default_rule='NEXT_UNNAMED_ARG').data
        1
        >>> UnnamedArgsParserMixin(r',"foo"', default_rule='NEXT_UNNAMED_ARG').data
        "foo"
        >>> UnnamedArgsParserMixin(r', null', default_rule='NEXT_UNNAMED_ARG').data
        None
        >>> UnnamedArgsParserMixin(r', FALSE', default_rule='NEXT_UNNAMED_ARG').data
        False
        >>> UnnamedArgsParserMixin(r', True', default_rule='NEXT_UNNAMED_ARG').data
        True

        """

        return children[1]

    @rule('NEXT_UNNAMED_ARG*')
    def visit_NEXT_UNNAMED_ARGS(self, node, children):
        """Unnamed arguments of a filter following the first one.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 1: list of instances of ``.resources.PosArg``.

        Returns
        -------
        list(.resources.PosArg)
            Instances of ``.resources.PosArg``.

        Example
        -------

        >>> UnnamedArgsParserMixin(r'', default_rule='NEXT_UNNAMED_ARGS').data
        []
        >>> UnnamedArgsParserMixin(r', 1', default_rule='NEXT_UNNAMED_ARGS').data
        [1]
        >>> UnnamedArgsParserMixin(r' , 1, 2', default_rule='NEXT_UNNAMED_ARGS').data
        [1, 2]
        >>> UnnamedArgsParserMixin(r' ,1,null, "foo"', default_rule='NEXT_UNNAMED_ARGS').data
        [1, None, "foo"]

        """

        return children

    @rule('VALUE')
    def visit_UNNAMED_ARG(self, node, children):
        """Unnamed argument of a filter.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: value of the unnamed arg

        Returns
        -------
        list(.resources.PosArg)
            Instances of ``.resources.PosArg``.

        Example
        -------

        >>> UnnamedArgsParserMixin(r'1', default_rule='UNNAMED_ARG').data
        1
        >>> UnnamedArgsParserMixin(r'"foo"', default_rule='UNNAMED_ARG').data
        "foo"
        >>> UnnamedArgsParserMixin(r'null', default_rule='UNNAMED_ARG').data
        None
        >>> UnnamedArgsParserMixin(r'FALSE', default_rule='UNNAMED_ARG').data
        False
        >>> UnnamedArgsParserMixin(r'True', default_rule='UNNAMED_ARG').data
        True

        """

        return self.PosArg(
            value=children[0],
        )


class ArgsParserMixin(NamedArgsParserMixin, UnnamedArgsParserMixin, BaseParser):
    """Parser mixin that provides rules to manage arguments in parentheses.

    To use it, add this mixin to the class bases, and use``OPTIONAL_ARGS`` in your rule(s).

    Example
    -------

    >>> ArgsParserMixin(r'()').data
    []
    >>> ArgsParserMixin(r'(1)').data
    [1]
    >>> ArgsParserMixin(r'(foo="bar")').data
    [foo="bar"]
    >>> ArgsParserMixin(r'(1, foo="bar")').data
    [1, foo="bar"]

    >>> class TestParser(ArgsParserMixin, BaseParser):
    ...     default_rule = 'ROOT'
    ...     @rule('IDENT OPTIONAL_ARGS')
    ...     def visit_ROOT(self, node, children):
    ...         return 'Ident "%s" with args: %s' % tuple(children)
    ...
    >>> TestParser('something(1,null, "foo")').data
    'Ident "something" with args: [1, None, "foo"]'

    """

    default_rule = 'OPTIONAL_ARGS'

    @rule('PAR_O OPTIONAL_ARGS_CONTENT PAR_C')
    def visit_OPTIONAL_ARGS(self, node, children):
        """The optional arguments of a filter.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: for ``PAR_O`` (opening parenthesis): ``None``.
            - 1: list of instances of subclasses of ``.resources.Arg``.
            - 2: for ``PAR_C`` (closing parenthesis): ``None``.

        Returns
        -------
        list(.resources.NamedArg)
            List of  instances of ``.resources.NamedArg`` or subclasses.

        Example
        -------

        >>> ArgsParserMixin(r'()', default_rule='OPTIONAL_ARGS').data
        []
        >>> ArgsParserMixin(r'(1)', default_rule='OPTIONAL_ARGS').data
        [1]
        >>> ArgsParserMixin(r'(foo="bar")', default_rule='OPTIONAL_ARGS').data
        [foo="bar"]
        >>> ArgsParserMixin(r'(1, foo="bar")', default_rule='OPTIONAL_ARGS').data
        [1, foo="bar"]

        """

        return children[1]

    @rule('ARGS?')
    def visit_OPTIONAL_ARGS_CONTENT(self, node, children):
        """The optional arguments of a filter (part inside the parentheses).

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 1: list of instances of ``.resources.NamedArg`` or subclasses.

        Returns
        -------
        list(.resources.NamedArg)
            List of  instances of ``.resources.NamedArg`` or subclasses.

        Example
        -------

        >>> ArgsParserMixin(r'', default_rule='OPTIONAL_ARGS_CONTENT').data
        []
        >>> ArgsParserMixin(r'1', default_rule='OPTIONAL_ARGS_CONTENT').data
        [1]
        >>> ArgsParserMixin(r'foo="bar"', default_rule='OPTIONAL_ARGS_CONTENT').data
        [foo="bar"]
        >>> ArgsParserMixin(r'1, foo="bar"', default_rule='OPTIONAL_ARGS_CONTENT').data
        [1, foo="bar"]

        """

        return children[0] if children else []

    @rule('UNNAMED_ARGS_AND_NAMED_ARGS / UNNAMED_ARGS / NAMED_ARGS')
    def visit_ARGS(self, node, children):
        """Arguments of a filter (part inside the parentheses).

        The arguments of a filter can be named or not. But unnamed ones must always come first.

        So this entry accept
            - unnamed args followed by named args
            - only unnamed args
            - only named args

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: list of instances of ``.resources.NamedArg`` or subclasses.

        Returns
        -------
        list(.resources.NamedArg)
            List of  instances of ``.resources.NamedArg`` or subclasses.

        Example
        -------

        >>> ArgsParserMixin(r'1', default_rule='ARGS').data
        [1]
        >>> ArgsParserMixin(r'1, 2', default_rule='ARGS').data
        [1, 2]
        >>> ArgsParserMixin(r'1,foo="bar"', default_rule='ARGS').data
        [1, foo="bar"]
        >>> ArgsParserMixin(r'1, 2, foo="bar", bar="qux"', default_rule='ARGS').data
        [1, 2, foo="bar", bar="qux"]
        >>> ArgsParserMixin(r'foo="bar"', default_rule='ARGS').data
        [foo="bar"]
        >>> ArgsParserMixin(r'foo="bar",bar="qux"', default_rule='ARGS').data
        [foo="bar", bar="qux"]

        """

        return children[0]

    @rule('UNNAMED_ARGS COM NAMED_ARGS')
    def visit_UNNAMED_ARGS_AND_NAMED_ARGS(self, node, children):
        """Unnamed arguments of a filter.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - o: list of instances of ``.resources.PosArg``.
            - 1: list of instances of ``.resources.NamedArg``.

        Returns
        -------
        list(.resources.NamedArg)
            List of  instances of ``.resources.NamedArg`` or subclasses.

        Example
        -------

        >>> ArgsParserMixin(r'1, foo="bar"', default_rule='UNNAMED_ARGS_AND_NAMED_ARGS').data
        [1, foo="bar"]
        >>> ArgsParserMixin(r'1, 2,foo="bar", bar="qux"',
        ... default_rule='UNNAMED_ARGS_AND_NAMED_ARGS').data
        [1, 2, foo="bar", bar="qux"]

        """

        return children[0] + children[2]


class FiltersParserMixin(ArgsParserMixin, BaseParser):
    """Parser mixin that provides rules to manage arguments in parentheses.

    To use it, add this mixin to the class bases, and use``OPTIONAL_ARGS`` in your rule(s).

    Example
    -------

    >>> FiltersParserMixin(r'foo').data
    [.foo]
    >>> FiltersParserMixin(r'foo().bar').data
    [.foo(), .bar]
    >>> FiltersParserMixin(r'foo().bar.baz(True, x=1)').data
    [.foo(), .bar, .baz(True, x=1)]
    >>> FiltersParserMixin(r'foo().bar.baz(True, x=1)').data
    [.foo(), .bar, .baz(True, x=1)]


    >>> class TestParser(FiltersParserMixin, BaseParser):
    ...     default_rule = 'ROOT'
    ...     @rule('IDENT DOT FILTERS')
    ...     def visit_ROOT(self, node, children):
    ...         return 'Ident "%s" filtered with %s' % (children[0], children[2])
    ...
    >>> TestParser('qux.foo().bar.baz(True, x=1)').data
    'Ident "qux" filtered with [.foo(), .bar, .baz(True, x=1)]'

    """

    default_rule = 'FILTERS'

    @rule('FILTER NEXT_FILTERS')
    def visit_FILTERS(self, node, children):
        """A succession of filters.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: instance of ``.resources.Filter``, the first filter
            - 1: list of instances of ``.resources.Filter``, the other filters

        Returns
        -------
        list(.resources.Filter)
            List of  instances of ``.resources.Filter``.

        Example
        -------

        >>> FiltersParserMixin(r'foo', default_rule='FILTERS').data
        [.foo]
        >>> FiltersParserMixin(r'foo().bar', default_rule='FILTERS').data
        [.foo(), .bar]
        >>> FiltersParserMixin(r'foo().bar.baz(True, x=1)', default_rule='FILTERS').data
        [.foo(), .bar, .baz(True, x=1)]

        """

        return [children[0]] + (children[1] or [])

    @rule('IDENT FILTER_ARGS')
    def visit_FILTER(self, node, children):
        """A filter, with optional arguments.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: string, name of the filter.
            - 1: list of instances of ``.resources.NamedArg``

        Returns
        -------
        .resources.Filter
            An instance of ``.resources.Filter`` with a name and a list of arguments.
            The list of arguments will be ``None`` if no parenthesis.

        Example
        -------

        >>> FiltersParserMixin(r'foo', default_rule='FILTER').data
        .foo
        >>> FiltersParserMixin(r'foo()', default_rule='FILTER').data
        .foo()
        >>> FiltersParserMixin(r'foo(1)', default_rule='FILTER').data
        .foo(1)
        >>> FiltersParserMixin(r'foo(1, bar="baz")', default_rule='FILTER').data
        .foo(1, bar="baz")

        """

        return self.Filter(
            name=children[0],
            args=children[1],
        )

    @rule('OPTIONAL_ARGS?')
    def visit_FILTER_ARGS(self, node, children):
        """The optional arguments of a filter.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: list of instances of ``.resources.NamedArg`` or subclasses,  or None

        Returns
        -------
        list(.resources.NamedArg)
            List of  instances of ``.resources.NamedArg`` or subclasses, or ``None`` if no
            parenthesis.

        Example
        -------

        >>> FiltersParserMixin(r'', default_rule='FILTER_ARGS').data

        >>> FiltersParserMixin(r'()', default_rule='FILTER_ARGS').data
        []
        >>> FiltersParserMixin(r'(1)', default_rule='FILTER_ARGS').data
        [1]
        >>> FiltersParserMixin(r'(1, bar="baz")', default_rule='FILTER_ARGS').data
        [1, bar="baz"]

        """

        return children[0] if children else None

    @rule('NEXT_FILTER*')
    def visit_NEXT_FILTERS(self, node, children):
        """Optional filters following a first one.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: list of instances of ``.resources.Filter``

        Returns
        -------
        list(.resources.Filter)
            List of  instances of ``.resources.Filter``.

        Example
        -------

        >>> FiltersParserMixin(r'.foo', default_rule='NEXT_FILTERS').data
        [.foo]
        >>> FiltersParserMixin(r'.foo().bar', default_rule='NEXT_FILTERS').data
        [.foo(), .bar]
        >>> FiltersParserMixin(r'.foo().bar.baz(True, x=1)', default_rule='NEXT_FILTERS').data
        [.foo(), .bar, .baz(True, x=1)]

        """

        return children

    @rule('DOT FILTER')
    def visit_NEXT_FILTER(self, node, children):
        """A filter that follow another one (so it starts with a dot).

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: for ``DOT`` (a dot): ``None``.
            - 1: instance of ``.resources.Filter``

        Returns
        -------
        .resources.Filter
            Instance of ``.resources.Filter``.

        Example
        -------

        >>> FiltersParserMixin(r'.foo', default_rule='NEXT_FILTER').data
        .foo
        >>> FiltersParserMixin(r'.foo(1)', default_rule='NEXT_FILTER').data
        .foo(1)

        """

        return children[1]
