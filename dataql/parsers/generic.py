"""``generic`` module of ``dataql.parsers``.

It provides the ``DataQLParser`` that is the most generic parser (actually the only one)
provided by the ``dataql`` library.

"""

from dataql.parsers.base import BaseParser, rule
from dataql.parsers.exceptions import ParserError
from dataql.parsers.mixins import FiltersWithSlicingParserMixin


class DataQLParser(FiltersWithSlicingParserMixin, BaseParser):
    """A parser using a opinionated language.

    Example
    -------

    >>> DataQLParser(r'''
    ... current_user {
    ...     name,
    ...     email.lowercase(),
    ...     friends.sorted(by='date').limit(10) [
    ...         name,
    ...         email
    ...     ],
    ... }
    ... ''').data
    <Object[current_user]>
      <Field[name] />
      <Field[email] .email.lowercase() />
      <List[friends] .friends.sorted(by="date").limit(10)>
        <Field[name] />
        <Field[email] />
      </List[friends]>
    </Object[current_user]>

    """

    default_rule = 'ROOT'

    def __init__(self, text, default_rule=None):
        """Override to try to get better error message.

        Below an example of the better message

        Example
        -------

        # First with a parser that will not try to get a better error message
        >>> query = 'foo {bar::baz}'
        >>> class WillNotDebugParser(DataQLParser):
        ...     debugging = True  # Will not try to debug, because marked as debugging
        >>> WillNotDebugParser(query) # doctest: +ELLIPSIS
        Traceback (most recent call last):
        dataql...ParserError:...line 1, column 5...text begins with: "{bar::baz}"

        # Now with a parser that will try to get a better error message
        >>> DataQLParser(query) # doctest: +ELLIPSIS
        Traceback (most recent call last):
        dataql...ParserError:...line 1, column 10...text begins with: ":baz}"


        """
        try:
            super().__init__(text, default_rule)
        except ParserError as ex:
            # If we are not yet in debugging mode, and the problem is at ROOT,
            # enter the debugging mode to expect a better error
            if not getattr(self, 'debugging', False) and ex.original_exception.expr.name == 'ROOT':
                DebugDataQLParser(text, default_rule)

            # If we were already in debugging mode, or the error happened not at the ROOT,
            # or the debugger didn't raise an exception, raise the original error.
            raise

    @rule('WS NAMED_RESOURCE WS')
    def visit_root(self, _, children):
        """The main node holding all the query.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``WS`` (whitespace): ``None``.
            - 1: for ``NAMED_RESOURCE``: an instance of a subclass of ``.resources.Resource``.
            - 2: for ``WS`` (whitespace): ``None``.

        Returns
        -------
        .resources.Resource
            An instance of a subclass of ``.resources.Resource``, with ``is_root`` set to ``True``.

        Example
        -------

        >>> data = DataQLParser(r'''
        ... foo
        ... ''', default_rule='ROOT').data
        >>> data
        <Field[foo] />
        >>> data.is_root
        True
        >>> data = DataQLParser(r'''
        ... bar[name]
        ... ''', default_rule='ROOT').data
        >>> data
        <List[bar]>
          <Field[name] />
        </List[bar]>
        >>> data.is_root
        True
        >>> data = DataQLParser(r'''
        ... baz{name}
        ... ''', default_rule='ROOT').data
        >>> data
        <Object[baz]>
          <Field[name] />
        </Object[baz]>
        >>> data.is_root
        True

        """

        resource = children[1]
        resource.is_root = True
        return resource

    @rule('NAMED_LIST / NAMED_OBJECT / FIELD')
    def visit_resource(self, _, children):
        """A resource in the query, could be a list, an object or a simple field.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: an instance of a subclass of ``.resources.Resource``, depending of the type that
              matches the rule.

        Returns
        -------
        .resources.Resource
            An instance of a subclass of ``.resources.Resource``, with ``is_root`` set to ``True``.
            It's a ``.resources.List`` if the query matches the ``LIST`` rule,
            ``.resources.Object`` if it matches the ``OBJECT`` rule, or ``.resources.Field`` if
            it matches `` the ``FIELD`` rule.

        Example
        -------

        >>> DataQLParser(r'foo', default_rule='RESOURCE').data
        <Field[foo] />
        >>> DataQLParser(r'bar[name]', default_rule='RESOURCE').data
        <List[bar]>
          <Field[name] />
        </List[bar]>
        >>> DataQLParser(r'baz{name}', default_rule='RESOURCE').data
        <Object[baz]>
          <Field[name] />
        </Object[baz]>

        """

        return children[0]

    @rule('OPTIONAL_RESOURCE_NAME RESOURCE')
    def visit_named_resource(self, _, children):
        """A resource in the query with its optional name.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``OPTIONAL_RESOURCE_NAME``: str, the name of the resource, or ``None`` if not
                 set in the query.
            - 1: for ``RESOURCE``: an instance of a subclass of ``.resources.Resource``.

        Returns
        -------
        .resources.Resource
            An instance of a subclass of ``.resources.Resource``, with its ``name`` field set
            to the name in the query if set.

        Example
        -------

        >>> DataQLParser(r'bar', default_rule='NAMED_RESOURCE').data
        <Field[bar] />
        >>> DataQLParser(r'foo:bar', default_rule='NAMED_RESOURCE').data
        <Field[foo] .bar />
        >>> DataQLParser(r'foo : bar', default_rule='NAMED_RESOURCE').data
        <Field[foo] .bar />

        """

        name, resource = children
        if name:
            resource.name = name
        return resource

    @rule('COM NAMED_RESOURCE')
    def visit_next_named_resource(self, _, children):
        """A resource in the query preceded by a coma, to define a resource following an other one.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``COM`` (coma): ``None``.
            - 1: for ``NAMED_RESOURCE``: an instance of a subclass of ``.resources.Resource``.

        Returns
        -------
        .resources.Resource
            An instance of a subclass of ``.resources.Resource``.

        Example
        -------

        >>> DataQLParser(r', foo', default_rule='NEXT_NAMED_RESOURCE').data
        <Field[foo] />
        >>> DataQLParser(r', foo:bar', default_rule='NEXT_NAMED_RESOURCE').data
        <Field[foo] .bar />
        >>> DataQLParser(r', bar[name]', default_rule='NEXT_NAMED_RESOURCE').data
        <List[bar]>
          <Field[name] />
        </List[bar]>

        """

        return children[1]

    @rule('NEXT_NAMED_RESOURCE*')
    def visit_next_named_resources(self, _, children):
        """A list of resource in the query following the first resource.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``NEXT_NAMED_RESOURCE*``: a list of instances of subclasses of
                ``.resources.Resource``.

        Returns
        -------
        list(.resources.Resource)
            A list of instances of subclasses of ``.resources.Resource``.

        Example
        -------

        >>> DataQLParser(r'', default_rule='NEXT_NAMED_RESOURCES').data
        []
        >>> DataQLParser(r', foo', default_rule='NEXT_NAMED_RESOURCES').data
        [<Field[foo] />]
        >>> DataQLParser(r', foo, bar:baz', default_rule='NEXT_NAMED_RESOURCES').data
        [<Field[foo] />, <Field[bar] .baz />]
        >>> DataQLParser(r', foo[name], bar{name}, baz', default_rule='NEXT_NAMED_RESOURCES').data
        [<List[foo]>
          <Field[name] />
        </List[foo]>, <Object[bar]>
          <Field[name] />
        </Object[bar]>, <Field[baz] />]

        """

        return children

    @rule('NAMED_RESOURCE NEXT_NAMED_RESOURCES COM?')
    def visit_named_content(self, _, children):
        """The content of a resource, composed of a list of resources.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``NAMED_RESOURCE``: first resource, instance of a subclass of
                 ``.resources.Resource``.
            - 1: for ``NEXT_NAMED_RESOURCES``: resources following the first one, list of instances
                 of subclasses of ``.resources.Resource``.
            - 2: for ``COM`` (trailing coma): ``None``.

        Returns
        -------
        list(.resources.Resource)
            A list of instances of subclasses of ``.resources.Resource``.

        Example
        -------

        >>> DataQLParser(r'foo', default_rule='NAMED_CONTENT').data
        [<Field[foo] />]
        >>> DataQLParser(r'foo:bar', default_rule='NAMED_CONTENT').data
        [<Field[foo] .bar />]
        >>> DataQLParser(r'foo,', default_rule='NAMED_CONTENT').data
        [<Field[foo] />]
        >>> DataQLParser(r'foo, bar', default_rule='NAMED_CONTENT').data
        [<Field[foo] />, <Field[bar] />]
        >>> DataQLParser(r'foo[name], bar{name}, baz, ', default_rule='NAMED_CONTENT').data
        [<List[foo]>
          <Field[name] />
        </List[foo]>, <Object[bar]>
          <Field[name] />
        </Object[bar]>, <Field[baz] />]

        """

        return [children[0]] + (children[1] or [])

    @rule('IDENT WS COL WS')
    def visit_resource_name(self, _, children):
        """The name of a resource, to force a name of a resource.

        Without it, the resource entry name will be used.

        It allows to query more that one time the same resource with different filters.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``IDENT``: string, the name of the resource.
            - 1: for ``COL`` (colon separating the name and its ): ``None``.

        Returns
        -------
        string
            The name of the resource.

        Example
        -------

        >>> DataQLParser(r'foo:', default_rule='RESOURCE_NAME').data
        'foo'
        >>> DataQLParser(r'foo :', default_rule='RESOURCE_NAME').data
        'foo'

        """

        return children[0]

    @rule('RESOURCE_NAME?')
    def visit_optional_resource_name(self, _, children):
        """The optional name of a resource, to force a name of a resource if set.

        Without it, the resource entry name will be used.

        It allows to query more that one time the same resource with different filters.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``RESOURCE_NAME?``: string, the name of the resource.

        Returns
        -------
        string
            The name of the resource, or None if not set.

        Example
        -------

        >>> DataQLParser(r'foo:', default_rule='OPTIONAL_RESOURCE_NAME').data
        'foo'
        >>> DataQLParser(r'', default_rule='OPTIONAL_RESOURCE_NAME').data

        """

        return children[0] if children and children[0] else None

    @rule('FILTERS')
    def visit_field(self, _, children):
        """A simple field.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``FILTERS``: list of instances of ``.resources.Field``.

        Returns
        -------
        .resources.Field
            An instance of ``.resources.Field`` with the correct name.

        Example
        -------

        >>> DataQLParser(r'foo', default_rule='FIELD').data
        <Field[foo] />
        >>> DataQLParser(r'foo(1)', default_rule='FIELD').data
        <Field[foo] .foo(1) />
        >>> DataQLParser(r'foo.bar()', default_rule='FIELD').data
        <Field[foo] .foo.bar() />
        """

        filters = children[0]
        return self.Field(getattr(filters[0], 'name', None), filters=filters)

    @rule('FILTERS OBJECT')
    def visit_named_object(self, _, children):
        """Manage an object, represented by a ``.resources.Object`` instance.

        This object is populated with data from the result of the ``FILTERS``.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``FILTERS``: list of instances of ``.resources.Field``.
            - 1: for ``OBJECT``: an ``Object`` resource

        Example
        -------

        >>> DataQLParser(r'foo{name}', default_rule='NAMED_OBJECT').data
        <Object[foo]>
          <Field[name] />
        </Object[foo]>

        """

        filters, resource = children
        resource.name = filters[0].name
        resource.filters = filters

        return resource

    @rule('CUR_O NAMED_CONTENT CUR_C')
    def visit_object(self, _, children):
        """Manage an object, represented by a ``.resources.Object`` instance.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``CUR_O`` (opening curly): ``None``.
            - 1: for ``CONTENT``: list of instances of subclasses of ``.resources.Resource``,
                 forming the content of the object/list
            - 2: for ``CUR_C`` (closing curly): ``None``.

        Example
        -------

        >>> DataQLParser(r'{name}', default_rule='OBJECT').data
        <Object>
          <Field[name] />
        </Object>

        """

        return self.Object(name=None, resources=children[1])

    @rule('FILTERS LIST')
    def visit_named_list(self, _, children):
        """Manage a list, represented by a ``.resources.List`` instance.

        This list is populated with data from the result of the ``FILTERS``.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``FILTERS``: list of instances of ``.resources.Field``.
            - 1: for ``LIST``: a ``List`` resource

        Example
        -------

        >>> DataQLParser(r'foo(1)[name]', default_rule='NAMED_LIST').data
        <List[foo] .foo(1)>
          <Field[name] />
        </List[foo]>

        """

        filters, resource = children
        resource.name = filters[0].name
        resource.filters = filters

        return resource

    @rule('BRA_O LIST_CONTENT BRA_C')
    def visit_list(self, _, children):
        """Manage a list, represented by a ``.resources.List`` instance.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``CUR_O`` (opening curly): ``None``.
            - 1: for ``CONTENT``: list of instances of subclasses of ``.resources.Resource``,
                 forming the content of the list.
            - 2: for ``CUR_C`` (closing curly): ``None``.

        Example
        -------

        >>> DataQLParser(r'[foo]', default_rule='LIST').data
        <List>
          <Field[foo] />
        </List>
        >>> DataQLParser(r'[foo,]', default_rule='LIST').data
        <List>
          <Field[foo] />
        </List>
        >>> DataQLParser(r'[foo, bar]', default_rule='LIST').data
        <List>
          <Field[foo] />
          <Field[bar] />
        </List>
        >>> DataQLParser(r'[foo, [bar]]', default_rule='LIST').data
        <List>
          <Field[foo] />
          <List>
            <Field[bar] />
          </List>
        </List>
        >>> DataQLParser(r'[[foo, bar], babar{baz, qux}, quz]', default_rule='LIST').data
        <List>
          <List>
            <Field[foo] />
            <Field[bar] />
          </List>
          <Object[babar]>
            <Field[baz] />
            <Field[qux] />
          </Object[babar]>
          <Field[quz] />
        </List>

        """

        return self.List(name=None, resources=children[1])

    @rule('NAMED_LIST / LIST / NAMED_OBJECT / OBJECT / FIELD')
    def visit_list_resource(self, _, children):
        """A resource in the query, could be a list, an object or a simple field.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: an instance of a subclass of ``.resources.Resource``, depending of the type that
              matches the rule.

        Returns
        -------
        .resources.Resource
            An instance of a subclass of ``.resources.Resource``, with ``is_root`` set to ``True``.
            It's a ``.resources.List`` if the query matches the ``LIST`` rule,
            ``.resources.Object`` if it matches the ``OBJECT`` rule, or ``.resources.Field`` if
            it matches `` the ``FIELD`` rule.

        Example
        -------

        >>> DataQLParser(r'foo', default_rule='RESOURCE').data
        <Field[foo] />
        >>> DataQLParser(r'bar[name]', default_rule='RESOURCE').data
        <List[bar]>
          <Field[name] />
        </List[bar]>
        >>> DataQLParser(r'baz{name}', default_rule='RESOURCE').data
        <Object[baz]>
          <Field[name] />
        </Object[baz]>

        """

        return children[0]

    @rule('COM LIST_RESOURCE')
    def visit_next_list_resource(self, _, children):
        """A resource in the query preceded by a coma, to define a resource following an other one.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``COM`` (coma): ``None``.
            - 1: for ``RESOURCE``: an instance of a subclass of ``.resources.Resource``.

        Returns
        -------
        .resources.Resource
            An instance of a subclass of ``.resources.Resource``.

        Example
        -------

        >>> DataQLParser(r', foo', default_rule='NEXT_LIST_RESOURCE').data
        <Field[foo] />
        >>> DataQLParser(r', bar[name]', default_rule='NEXT_LIST_RESOURCE').data
        <List[bar]>
          <Field[name] />
        </List[bar]>
        >>> DataQLParser(r', bar{name}', default_rule='NEXT_LIST_RESOURCE').data
        <Object[bar]>
          <Field[name] />
        </Object[bar]>

        """

        return children[1]

    @rule('NEXT_LIST_RESOURCE*')
    def visit_next_list_resources(self, _, children):
        """A list of resource in the query following the first resource.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``NEXT_RESOURCE*``: a list of instances of subclasses of
                ``.resources.Resource``.

        Returns
        -------
        list(.resources.Resource)
            A list of instances of subclasses of ``.resources.Resource``.

        Example
        -------

        >>> DataQLParser(r'', default_rule='NEXT_LIST_RESOURCES').data
        []
        >>> DataQLParser(r', foo', default_rule='NEXT_LIST_RESOURCES').data
        [<Field[foo] />]
        >>> DataQLParser(r', foo[name], bar{name}, baz', default_rule='NEXT_LIST_RESOURCES').data
        [<List[foo]>
          <Field[name] />
        </List[foo]>, <Object[bar]>
          <Field[name] />
        </Object[bar]>, <Field[baz] />]

        """

        return children

    @rule('LIST_RESOURCE NEXT_LIST_RESOURCES COM?')
    def visit_list_content(self, _, children):
        """The content of a resource, composed of a list of resources.

        Resources have no name: we don't expect a dict in return, but a single item (if
        only one resource) or a list (if many resource)

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``RESOURCE``: first resource, instance of a subclass of
                 ``.resources.Resource``.
            - 1: for ``NEXT_RESOURCES``: resources following the first one, list of instances
                 of subclasses of ``.resources.Resource``.
            - 2: for ``COM`` (trailing coma): ``None``.

        Returns
        -------
        list(.resources.Resource)
            A list of instances of subclasses of ``.resources.Resource``.

        Example
        -------

        >>> DataQLParser(r'foo', default_rule='LIST_CONTENT').data
        [<Field[foo] />]
        >>> DataQLParser(r'foo,', default_rule='LIST_CONTENT').data
        [<Field[foo] />]
        >>> DataQLParser(r'foo, bar', default_rule='LIST_CONTENT').data
        [<Field[foo] />, <Field[bar] />]
        >>> DataQLParser(r'foo[name], bar{name}, baz, ', default_rule='LIST_CONTENT').data
        [<List[foo]>
          <Field[name] />
        </List[foo]>, <Object[bar]>
          <Field[name] />
        </Object[bar]>, <Field[baz] />]

        """

        return [children[0]] + (children[1] or [])



class DebugDataQLParser(DataQLParser):
    """Parser to use to get better error for ``IncompleteParseError`` exceptions.

    If the root resource is a list or an object but there is an error, ``parsimonious``
    choose the third resource type, the field, and ignore the rest of the query starting at
    ``[`` or ``{``, raising an ``IncompleteParseError``.

    This parser extends the ``DataQLParser`` by allowing only list or object as the first
    resource, to try to get a better error.

    """

    debugging = True

    @rule('WS NAMED_ROOT_RESOURCE WS')
    def visit_root(self, *args):
        """Override the ROOT rule to accept a NAMED_ROOT_RESOURCE instead of a NAMED_RESOURCE."""
        return super().visit_root(*args)

    @rule('OPTIONAL_RESOURCE_NAME ROOT_RESOURCE')
    def visit_named_root_resource(self, *args):
        """New rule to accept as ROOT rule a optional name and a ROOT_RESOURCE."""
        return super().visit_named_resource(*args)

    @rule('NAMED_LIST / NAMED_OBJECT')
    def visit_root_resource(self, *args):
        """New rule to accept only LIST or OBJECT as root resource."""
        return super().visit_resource(*args)
