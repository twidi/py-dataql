"""``mixins`` module of ``dataql.parsers``.

It provides some mixin to ease the creation of complex parsers:
- NamedArgsParserMixin : manage named arguments
- UnnamedArgsParserMixin : manage unnamed arguments
- ArgsParserMixin : manage arguments (unnamed and named ones)
- SliceParserMixin : manage slicing of iterables (think ``[start:stop:step]`` or ``[index]``)
- FiltersParserMixin : manage filters (many successive filters, each filter is an identifier with
                       or without arguments)

"""

from abc import ABCMeta

from dataql.parsers.base import BaseParser, rule


class NamedArgsParserMixin(BaseParser, metaclass=ABCMeta):
    """Parser mixin that provides rules to manage named arguments.

    A list of named arguments is a list of at least one named argument separated by a comma.
    An named argument is an identifier followed by an operator, followed by a value, ie a number,
    a string, or a null, false or true value.

    To use it, add this mixin to the class bases, and use ``NAMED_ARGS`` in your rule(s).

    Results
    -------
    list of NamedArg
        The output of the ``visit_named_args`` is a list of ``NamedArg`` objects.
        The list may be empty.

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
    ...     def visit_root(self, _, children):
    ...         return 'Content with named args: %s' % children[1]
    ...
    >>> TestParser('(foo=TRUE, bar ="BAZ",quz=null)').data
    'Content with named args: [foo=True, bar="BAZ", quz=None]'

    """

    default_rule = 'NAMED_ARGS'

    @rule('NAMED_ARG NEXT_NAMED_ARGS')
    def visit_named_args(self, _, children):
        """Named arguments of a filter.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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
    def visit_next_named_arg(self, _, children):
        """Named argument of a filter following a previous one (so, preceded by a comma).

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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
    def visit_next_named_args(self, _, children):
        """Named arguments of a filter following the first one.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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
    def visit_named_arg(self, _, children):
        """Named argument of a filter.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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


class UnnamedArgsParserMixin(BaseParser, metaclass=ABCMeta):
    """Parser mixin that provides rules to manage unnamed arguments.

    A list of unnamed arguments is a list of at least one unnamed argument separated by a comma.
    An unnamed argument is a value, ie a number, a string, or a null, false or true value.

    To use it, add this mixin to the class bases, and use ``UNNAMED_ARGS`` in your rule(s).

    Results
    -------
    list of PosArg
        The output of the ``visit_unnamed_args`` is a list of ``PosArg`` objects.
        The list may be empty.

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
    ...     def visit_root(self, _, children):
    ...         return 'Content with unnamed args: %s' % children[1]
    ...
    >>> TestParser('(1,null, "foo")').data
    'Content with unnamed args: [1, None, "foo"]'

    """

    default_rule = 'UNNAMED_ARGS'

    @rule('UNNAMED_ARG NEXT_UNNAMED_ARGS')
    def visit_unnamed_args(self, _, children):
        """Unnamed arguments of a filter.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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
    def visit_next_unnamed_arg(self, _, children):
        """Unnamed argument of a filter following a previous one (so, preceded by a comma).

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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
    def visit_next_unnamed_args(self, _, children):
        """Unnamed arguments of a filter following the first one.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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
    def visit_unnamed_arg(self, _, children):
        """Unnamed argument of a filter.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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


class ArgsParserMixin(NamedArgsParserMixin, UnnamedArgsParserMixin, BaseParser,
                      metaclass=ABCMeta):
    """Parser mixin that provides rules to manage arguments in parentheses.

    To use it, add this mixin to the class bases, and use``OPTIONAL_ARGS`` in your rule(s).

    Results
    -------
    list of subclasses of Arg
        The output of the ``visit_optional_args`` is a list of subclasses of ``PosArg`` then
        ``NamedArg`` objects. The list may be empty.

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
    ...     def visit_root(self, _, children):
    ...         return 'Ident "%s" with args: %s' % tuple(children)
    ...
    >>> TestParser('something(1,null, "foo")').data
    'Ident "something" with args: [1, None, "foo"]'

    """

    default_rule = 'OPTIONAL_ARGS'

    @rule('PAR_O OPTIONAL_ARGS_CONTENT PAR_C')
    def visit_optional_args(self, _, children):
        """The optional arguments of a filter.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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
    def visit_optional_args_content(self, _, children):
        """The optional arguments of a filter (part inside the parentheses).

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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

    @rule('ALL_ARGS / UNNAMED_ARGS / NAMED_ARGS')
    def visit_args(self, _, children):
        """Arguments of a filter (part inside the parentheses).

        The arguments of a filter can be named or not. But unnamed ones must always come first.

        So this entry accept
            - unnamed args followed by named args
            - only unnamed args
            - only named args

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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
    def visit_all_args(self, _, children):
        """Unnamed and named arguments of a filter.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - o: list of instances of ``.resources.PosArg``.
            - 1: list of instances of ``.resources.NamedArg``.

        Returns
        -------
        list(.resources.NamedArg)
            List of  instances of ``.resources.NamedArg`` or subclasses.

        Example
        -------

        >>> ArgsParserMixin(r'1, foo="bar"', default_rule='ALL_ARGS').data
        [1, foo="bar"]
        >>> ArgsParserMixin(r'1, 2,foo="bar", bar="qux"', default_rule='ALL_ARGS').data
        [1, 2, foo="bar", bar="qux"]

        """

        return children[0] + children[2]


class SliceParserMixin(BaseParser, metaclass=ABCMeta):
    """Parser mixin that manage a list slicing, ie ``[x:y:z]`` of just an item like ``[1]``.

    To use it, add this mixin to the class bases, and use``SLICE`` in your rule(s).

    Results
    -------
    slice or number
        The output of the ``visit_slice`` method is a ``slice`` python object when asking
        for a slice of a list, of a single number when asking for a single entry.

    Example
    -------

    >>> SliceParserMixin('[1]', default_rule='SLICE').data
    1
    >>> SliceParserMixin('[:]', default_rule='SLICE').data
    slice(None, None, None)
    >>> SliceParserMixin('[1:]', default_rule='SLICE').data
    slice(1, None, None)
    >>> SliceParserMixin('[1:2:3]', default_rule='SLICE').data
    slice(1, 2, 3)

    """

    default_rule = 'SLICE'

    @rule('BRA_O SLICE_CONTENT BRA_C')
    def visit_slice(self, _, children):
        """A slice or number contained in brackets (``[]``)

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``BRA_O`` (opening bracket): ``None``.
            - 1: slice or number.
            - 2: for ``BRA_C`` (closing bracket): ``None``.

        Returns
        -------
        slice or number
            The slice or number got from ``children[1]``

        Example
        -------

        >>> SliceParserMixin('[1]', default_rule='SLICE').data
        1
        >>> SliceParserMixin('[:]', default_rule='SLICE').data
        slice(None, None, None)
        >>> SliceParserMixin('[1:]', default_rule='SLICE').data
        slice(1, None, None)
        >>> SliceParserMixin('[1:2:3]', default_rule='SLICE').data
        slice(1, 2, 3)

        """

        return children[1]

    @rule('FULL_SLICE / NB')
    def visit_slice_content(self, _, children):
        """The content of a slice (to be in brackets)

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: slice or number

        Returns
        -------
        slice or number
            The slice or number got from ``children[1]``

        Example
        -------

        >>> SliceParserMixin('1', default_rule='SLICE_CONTENT').data
        1
        >>> SliceParserMixin(':', default_rule='SLICE_CONTENT').data
        slice(None, None, None)
        >>> SliceParserMixin('1:', default_rule='SLICE_CONTENT').data
        slice(1, None, None)
        >>> SliceParserMixin('1:2:3', default_rule='SLICE_CONTENT').data
        slice(1, 2, 3)

        """

        return children[0]

    @rule('OPTIONAL_NB WS COL WS OPTIONAL_NB WS OPTIONAL_SLICE_STEP')
    def visit_full_slice(self, _, children):
        """The content of a slice (to be in brackets) with at least one colon.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: an optional number to use as the ``start`` attribute of a ``slice`` object.
            - 1: for ``WS``, optional white space: ``None``
            - 2: for ``COL``, the colon character: ``None``
            - 3: for ``WS``, optional white space: ``None``
            - 4: an optional number to use as the ``stop`` attribute of a ``slice`` object.
            - 5: for ``WS``, optional white space: ``None``
            - 6: an optional number to use as the ``step`` attribute of a ``slice`` object,
                 got from the ``OPTIONAL_SLICE_STEP`` rule (which expects a colon and/or a number)

        Returns
        -------
        slice
            A ``slice`` object with ``start``, ``stop`` and ``step`` arguments set from children.

        Example
        -------

        >>> SliceParserMixin(':', default_rule='FULL_SLICE').data
        slice(None, None, None)
        >>> SliceParserMixin('::', default_rule='FULL_SLICE').data
        slice(None, None, None)
        >>> SliceParserMixin('1:', default_rule='FULL_SLICE').data
        slice(1, None, None)
        >>> SliceParserMixin(':2', default_rule='FULL_SLICE').data
        slice(None, 2, None)
        >>> SliceParserMixin('1:2', default_rule='FULL_SLICE').data
        slice(1, 2, None)
        >>> SliceParserMixin('::3', default_rule='FULL_SLICE').data
        slice(None, None, 3)
        >>> SliceParserMixin(':2:3', default_rule='FULL_SLICE').data
        slice(None, 2, 3)
        >>> SliceParserMixin('1::3', default_rule='FULL_SLICE').data
        slice(1, None, 3)
        >>> SliceParserMixin('1:2:3', default_rule='FULL_SLICE').data
        slice(1, 2, 3)

        """

        return slice(children[0], children[4], children[6])

    @rule('SLICE_STEP?')
    def visit_optional_slice_step(self, _, children):
        """The optional slice step for a slice (to be in bracket).

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: an optional number to use as the ``step`` attribute of a ``slice`` object,
                 got from the ``SLICE_STEP`` rule (which expects a colon and/or a number)

        Returns
        -------
        number or None
            The number to use as the ``step`` attribute of a ``slice`` object.

        Example
        -------

        >>> SliceParserMixin('', default_rule='OPTIONAL_SLICE_STEP').data

        >>> SliceParserMixin(':', default_rule='OPTIONAL_SLICE_STEP').data

        >>> SliceParserMixin(':1', default_rule='OPTIONAL_SLICE_STEP').data
        1

        """

        return children[0] if children else None

    @rule('COL WS OPTIONAL_NB')
    def visit_slice_step(self, _, children):
        """The optional slice step for a slice (to be in bracket).

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``COL``, the colon character: ``None``
            - 1: for ``WS``, optional white space: ``None``
            - 2: an optional number to use as the ``step`` attribute of a ``slice`` object

        Returns
        -------
        number or None
            The number to use as the ``step`` attribute of a ``slice`` object.

        Example
        -------

        >>> SliceParserMixin(':', default_rule='SLICE_STEP').data

        >>> SliceParserMixin(':1', default_rule='SLICE_STEP').data
        1

        >>> SliceParserMixin(': 2', default_rule='SLICE_STEP').data
        2

        """

        return children[2] if len(children) > 2 else None


class FiltersParserMixin(ArgsParserMixin, BaseParser, metaclass=ABCMeta):
    """Parser mixin that provides rules to manage arguments in parentheses.

    To use it, add this mixin to the class bases, and use``FILTERS`` in your rule(s).

    Results
    -------
    list of Filter
        The output of the ``visit_filters`` is a list of ``Filter`` objects.
        The list may be empty.

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
    ...     def visit_root(self, _, children):
    ...         return 'Ident "%s" filtered with %s' % (children[0], children[2])
    ...
    >>> TestParser('qux.foo().bar.baz(True, x=1)').data
    'Ident "qux" filtered with [.foo(), .bar, .baz(True, x=1)]'

    """

    default_rule = 'FILTERS'

    @rule('FIRST_FILTER NEXT_FILTERS')
    def visit_filters(self, _, children):
        """A succession of filters.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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

    @rule('FILTER')
    def visit_first_filter(self, _, children):
        """The first filter, so not preceded by a dot.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: A``Filter`` resource.

        Returns
        -------
        .resources.Filter
            An instance of ``Filter``.

        Example
        -------

        >>> FiltersParserMixin('foo', default_rule='FIRST_FILTER').data
        .foo

        """

        return children[0]

    @rule('IDENT FILTER_ARGS')
    def visit_filter(self, _, children):
        """A filter, with optional arguments.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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
    def visit_filter_args(self, _, children):
        """The optional arguments of a filter.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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
    def visit_next_filters(self, _, children):
        """Optional filters following a first one.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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
    def visit_next_filter(self, _, children):
        """A filter that follow another one (so it starts with a dot).

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
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


class FiltersWithSlicingParserMixin(FiltersParserMixin, SliceParserMixin, metaclass=ABCMeta):
    """Parser mixin that provides rules to manage filters, including slices.

    To use it, add this mixin to the class bases, and use``FILTERS`` in your rule(s).

    Results
    -------
    list of Filter or SliceFilter
        The output of the ``visit_filters`` is a list of ``Filter`` or ``SliceFilter`` objects.
        The list may be empty.

    Example
    -------

    >>> FiltersWithSlicingParserMixin(r'foo').data
    [.foo]
    >>> FiltersWithSlicingParserMixin(r'foo.0').data
    [.foo, [0]]
    >>> FiltersWithSlicingParserMixin(r'foo.1').data
    [.foo, [1]]
    >>> FiltersWithSlicingParserMixin(r'foo[0:2].bar').data
    [.foo, [0:2], .bar]
    >>> FiltersWithSlicingParserMixin(r'0').data
    [[0]]
    >>> FiltersWithSlicingParserMixin(r'0.foo').data
    [[0], .foo]
    >>> FiltersWithSlicingParserMixin(r'[1]').data
    [[1]]
    >>> FiltersWithSlicingParserMixin(r'[0:2]').data
    [[0:2]]
    >>> FiltersWithSlicingParserMixin(r'[0:2].foo').data
    [[0:2], .foo]

    """

    @rule('NB')
    def visit_nb_filter(self, _, children):
        """A number used as a filter, to retrieve an entry in a list.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: a number

        Returns
        -------
        .resources.SliceFilter
            An instance of ``SliceFilter`` filed with the number as index, and no slice.

        Example
        -------

        >>> FiltersWithSlicingParserMixin('1', default_rule='NB_FILTER').data
        [1]

        """

        return self.SliceFilter(children[0])

    @rule('SLICE')
    def visit_slice_filter(self, _, children):
        """A slice, to retrieve 0, 1 or more elements from a list.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: a ``slice`` object or a number

        Returns
        -------
        .resources.SliceFilter
            An instance of ``SliceFilter`` using the the slice or number.

        Example
        -------

        >>> FiltersWithSlicingParserMixin('[1]', default_rule='SLICE_FILTER').data
        [1]
        >>> FiltersWithSlicingParserMixin('[1:2]', default_rule='SLICE_FILTER').data
        [1:2]

        """

        return self.SliceFilter(children[0])

    @rule('SLICE_FILTER / NB_FILTER / FILTER')
    def visit_first_filter(self, _, children):
        """The first filter, so not preceded by a dot, could be a slice (or number) or a filter.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: a ``slice`` object or a ``Filter`` resource.

        Returns
        -------
        Filter or SliceFilter
            An instance of ``Filter`` if a filter, or ``SliceFilter`` if a number or a slice.

        Example
        -------

        >>> FiltersWithSlicingParserMixin('1', default_rule='FIRST_FILTER').data
        [1]
        >>> FiltersWithSlicingParserMixin('[1]', default_rule='FIRST_FILTER').data
        [1]
        >>> FiltersWithSlicingParserMixin('[1:2]', default_rule='FIRST_FILTER').data
        [1:2]
        >>> FiltersWithSlicingParserMixin('foo', default_rule='FIRST_FILTER').data
        .foo

        """

        return children[0]

    @rule('DOT DOTTABLE_FILTER')
    def visit_dotted_filter(self, _, children):
        """A filter, preceded by a dot, could be a number (not a full slice) or a filter.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``DOT`` (a dot): ``None``.
            - 1: a ``Filter`` or ``SliceFilter`` (with only ``index`` set)

        Returns
        -------
        Filter or SliceFilter
            An instance of ``Filter`` if a filter, or ``SliceFilter`` if a number.

        Example
        -------

        >>> FiltersWithSlicingParserMixin('.1', default_rule='DOTTED_FILTER').data
        [1]
        >>> FiltersWithSlicingParserMixin('.foo', default_rule='DOTTED_FILTER').data
        .foo

        """

        return children[1]

    @rule('NB_FILTER / FILTER')
    def visit_dottable_filter(self, _, children):
        """A filter that can be preceded by a dot. Could be a number (not full slice) or a filter.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: a ``Filter`` or ``SliceFilter`` (with only ``index`` set)

        Returns
        -------
        Filter or SliceFilter
            An instance of ``Filter`` if a filter, or ``SliceFilter`` if a number.

        Example
        -------

        >>> FiltersWithSlicingParserMixin('1', default_rule='DOTTABLE_FILTER').data
        [1]
        >>> FiltersWithSlicingParserMixin('foo', default_rule='DOTTABLE_FILTER').data
        .foo

        """

        return children[0]

    @rule('SLICE_FILTER / DOTTED_FILTER')
    def visit_next_filter(self, _, children):
        """A filter, not the first one. Could be a slice or a filter (or number) preceded by a dot.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: a ``Filter`` or ``SliceFilter``

        Returns
        -------
        Filter or SliceFilter
            An instance of ``Filter`` if a filter, or ``SliceFilter`` if a number or a slice.

        Example
        -------

        >>> FiltersWithSlicingParserMixin('[1]', default_rule='NEXT_FILTER').data
        [1]
        >>> FiltersWithSlicingParserMixin('[1:2]', default_rule='NEXT_FILTER').data
        [1:2]
        >>> FiltersWithSlicingParserMixin('.1', default_rule='NEXT_FILTER').data
        [1]
        >>> FiltersWithSlicingParserMixin('.foo', default_rule='NEXT_FILTER').data
        .foo

        """

        return children[0]
