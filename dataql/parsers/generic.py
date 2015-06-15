"""``generic`` module of ``dataql.parsers``.

It provides the ``DataQLParser`` that is the most generic parser (actually the only one)
provided by the ``dataql`` library.

"""

from dataql.parsers.base import BaseParser, rule
from dataql.parsers.mixins import FiltersParserMixin


class DataQLParser(FiltersParserMixin, BaseParser):
    """A parser using a opinionated language

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
      <Field[email] email.lowercase() />
      <List[friends] friends.sorted(by="date").limit(10)>
        <Field[name] />
        <Field[email] />
      </List[friends]>
    </Object[current_user]>

    """

    default_rule = 'ROOT'

    @rule('WS NAMED_RESOURCE WS')
    def visit_ROOT(self, node, children):
        """The main node holding all the query.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
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

    @rule('LIST / OBJECT / FIELD')
    def visit_RESOURCE(self, node, children):
        """A resource in the query, could be a list, an object or a simple field.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
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
    def visit_NAMED_RESOURCE(self, node, children):
        """A resource in the query with its optional name.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: for ``OPTIONAL_RESOURCE_NAME``: str, the name of the resource, or ``None`` if not
                 set in the query.
            - 1: for ``RESOURCE``: an instance of a subclass of ``.resources.Resource``.

        Returns
        -------
        .resources.Resource
            An instance of a subclass of ``.resources.Resource``, with its ``entry_name`` field set
            to the name in the query if set.

        Example
        -------

        >>> DataQLParser(r'bar', default_rule='NAMED_RESOURCE').data
        <Field[bar] />
        >>> DataQLParser(r'foo:bar', default_rule='NAMED_RESOURCE').data
        <Field[foo] bar />

        """

        entry_name, resource = children
        if entry_name:
            resource.entry_name = entry_name
        return resource

    @rule('COM NAMED_RESOURCE')
    def visit_NEXT_RESOURCE(self, node, children):
        """A resource in the query preceded by a coma, to define a resource following an other one.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: for ``COM`` (coma): ``None``.
            - 1: for ``NAMED_RESOURCE``: an instance of a subclass of ``.resources.Resource``.

        Returns
        -------
        .resources.Resource
            An instance of a subclass of ``.resources.Resource``.

        Example
        -------

        >>> DataQLParser(r', foo', default_rule='NEXT_RESOURCE').data
        <Field[foo] />
        >>> DataQLParser(r', bar[name]', default_rule='NEXT_RESOURCE').data
        <List[bar]>
          <Field[name] />
        </List[bar]>

        """

        return children[1]

    @rule('NEXT_RESOURCE*')
    def visit_NEXT_RESOURCES(self, node, children):
        """A list of resource in the query following the first resource.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: for ``NEXT_RESOURCE*``: a list of instances of subclasses of
                ``.resources.Resource``.

        Returns
        -------
        list(.resources.Resource)
            A list of instances of subclasses of ``.resources.Resource``.

        Example
        -------

        >>> DataQLParser(r'', default_rule='NEXT_RESOURCES').data
        []
        >>> DataQLParser(r', foo', default_rule='NEXT_RESOURCES').data
        [<Field[foo] />]
        >>> DataQLParser(r', foo, bar', default_rule='NEXT_RESOURCES').data
        [<Field[foo] />, <Field[bar] />]
        >>> DataQLParser(r', foo[name], bar{name}, baz', default_rule='NEXT_RESOURCES').data
        [<List[foo]>
          <Field[name] />
        </List[foo]>, <Object[bar]>
          <Field[name] />
        </Object[bar]>, <Field[baz] />]

        """

        return children

    @rule('RESOURCE NEXT_RESOURCES COM?')
    def visit_CONTENT(self, node, children):
        """The content of a resource, composed of a list of resources.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
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

        >>> DataQLParser(r'foo', default_rule='CONTENT').data
        [<Field[foo] />]
        >>> DataQLParser(r'foo,', default_rule='CONTENT').data
        [<Field[foo] />]
        >>> DataQLParser(r'foo, bar', default_rule='CONTENT').data
        [<Field[foo] />, <Field[bar] />]
        >>> DataQLParser(r'foo[name], bar{name}, baz, ', default_rule='CONTENT').data
        [<List[foo]>
          <Field[name] />
        </List[foo]>, <Object[bar]>
          <Field[name] />
        </Object[bar]>, <Field[baz] />]

        """

        return [children[0]] + (children[1] or [])

    @rule('IDENT COL')
    def visit_RESOURCE_NAME(self, node, children):
        """The name of a resource, to force a name of a resource.

        Without it, the resource entry name will be used.

        It allows to query more that one time the same resource with different filters.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
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

        """

        name, _ = children
        return name

    @rule('RESOURCE_NAME?')
    def visit_OPTIONAL_RESOURCE_NAME(self, node, children):
        """The optional name of a resource, to force a name of a resource if set.

        Without it, the resource entry name will be used.

        It allows to query more that one time the same resource with different filters.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
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
    def visit_FIELD(self, node, children):
        """A simple field.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
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
        <Field[foo] foo(1) />
        >>> DataQLParser(r'foo.bar()', default_rule='FIELD').data
        <Field[foo] foo.bar() />
        """

        return self.filters_to_resource(children[0], self.Field)

    def filters_to_resource(self, filters, klass, **kwargs):
        """Helper to create a resource taking its name and args from the first filter.

        This remove the first filter from the list of filters

        """

        first_filter = filters.pop(0)

        attrs = {
            'name': first_filter.name,
            'entry_name': first_filter.name,
            'args': first_filter.args,
            'filters': filters,
        }
        attrs.update(kwargs)

        return klass(**attrs)

    def visit_subresource(self, klass, node, children):
        """Helper to create a List or Object.

        The name of the resource is the name of the first filter. And if this first filter doesn't
        have any argument, it is removed.

        Arguments
        ---------
        klass: The class for which we want an instance
        node : parsimonious.nodes.Node.
        children : list
            - 0: for ``FILTERS``: list of instances of ``.resources.Field``.
            - 1: for ``CUR_O`` or ``BRA_O`` (opening curly/bracket): ``None``.
            - 2: for ``CONTENT``: list of instances of subclasses of ``.resources.Resource``,
                 forming the content of the object/list
            - 3: for ``CUR_C`` or ``BRA_C`` (closing curly/bracket): ``None``.

        Example
        -------

        >>> DataQLParser(r'foo{name}', default_rule='OBJECT').data
        <Object[foo]>
          <Field[name] />
        </Object[foo]>
        >>> DataQLParser(r'foo(1)[name]', default_rule='LIST').data
        <List[foo] foo(1)>
          <Field[name] />
        </List[foo]>

        """

        return self.filters_to_resource(children[0], klass)

    @rule('FILTERS CUR_O CONTENT CUR_C')
    def visit_OBJECT(self, node, children):
        """Manage an object, represented by a ``.resources.Object`` instance.

        The first filter is removed to fill the name and args of the resource. See
        ``filters_to_resource`` for more details.


        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: for ``FILTERS``: list of instances of ``.resources.Field``.
            - 1: for ``CUR_O`` (opening curly): ``None``.
            - 2: for ``CONTENT``: list of instances of subclasses of ``.resources.Resource``,
                 forming the content of the object/list
            - 3: for ``CUR_C`` (closing curly): ``None``.

        Example
        -------

        >>> DataQLParser(r'foo{name}', default_rule='OBJECT').data
        <Object[foo]>
          <Field[name] />
        </Object[foo]>

        """

        return self.filters_to_resource(children[0], self.Object, resources=children[2])

    @rule('FILTERS BRA_O CONTENT BRA_C')
    def visit_LIST(self, node, children):
        """Manage a list, represented by a ``.resources.List`` instance.

        The first filter is removed to fill the name and args of the resource. See
        ``filters_to_resource`` for more details.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        children : list
            - 0: for ``FILTERS``: list of instances of ``.resources.Field``.
            - 1: for ``BRA_O`` (opening bracket): ``None``.
            - 2: for ``CONTENT``: list of instances of subclasses of ``.resources.Resource``,
                 forming the content of the object/list
            - 3: for ``BRA_C`` (closing bracket): ``None``.

        Example
        -------

        >>> DataQLParser(r'foo(1)[name]', default_rule='LIST').data
        <List[foo] foo(1)>
          <Field[name] />
        </List[foo]>

        """

        return self.filters_to_resource(children[0], self.List, resources=children[2])
