"""``resources`` module of ``dataql``.

It provides the different classes that are used to store a usable structure from a query
parsed by a dataql parser.

We have three resources. Each one can have zero to many filters, but at least a name and maybe a
different "entry_name" (if given, it will be the name used in the result instead of the identifier)

The name of the resource if the attribute that will be retrieved from a value.

The three resources are:

- ``Field`` : a simple field. A parser may cast it into a simple value (string, number, null,
              false or true)
- ``Object`` : the value is an object from which we want some fields.
- ``List`` : the value is an iterable, and for each entry we want some fields

A resource has a name, but can also have filters (``Filter`` class). The attribute is retrieved
from the value using the name (and the arguments if any, ``NamedArg`` and ``PosArg``), and then
the first filter is applied to this value, then the next filter from the result of the first
filter, and so one.
When all filters are applied, the value is casted (number, string... for ``Field``, dictionary
for ``Object`` and list for ``List``.


To use subclasses of the classes defined here, they must be set on the parser:

    class MyList(List):
        pass

    class MyParser(BaseParser):
        List = MyList

"""

__all__ = ('Field', 'List', 'Object', 'Filter', 'NamedArg', 'PosArg')


class WithArgsMixin:
    """Mixin to manage entities accepting arguments.

    Attributes
    ----------
    args : list, or None
        If ``None``, the entity is marked as not taking any argument, ie not callable.
        If a list, it's the list of subclasses of ``Arg`` to use as arguments.

    """

    def __init__(self, **kwargs):
        """Save arguments in the ``args`` attribute and mark self as the args parent."""
        self.args = kwargs['args']

        if self.args:
            for arg in self.args:
                arg.set_parent(self)

    def get_args_and_kwargs(self):
        """Return a list and a dict usable as ``*args, **kwargs`` to pass to a callable."

        If the entity is known to not accept arguments (``self.args`` is ``None``), then this
        method returns ``None`` for both args and kwargs.s

        Returns
        -------
        tuple (list or None, dict or None)
            A tuple with as first value, the list of positioned arguments (or ``None``), and as
            second value the dict of named arguments (or ``None``)

        """

        args = None
        kwargs = None

        if self.args:
            args = []
            kwargs = {}
            for arg in self.args:
                if arg.is_named:
                    kwargs[arg.arg] = arg.value
                else:
                    args.append(arg.value)

        return args, kwargs


class Resource(WithArgsMixin):
    """Base class for all resource classes.

    A resource is mainly a attribute to retrieve from a value (via a solver).
    This attribute may be callable, so the resource may have arguments.
    The resource can also have filters to apply the the attribute.

    Attributes
    ----------
    name : string
        The name of the attribute to get from a value.
    entry_name : string
        The name to use in the result instead of the ``name`` attribute. If not defined, the
        ``name`` attribute is used. Allow to retrieve the same attribute many times (for example
        with different filters) and have them all in the final result under different names.
    is_root : boolean
        ``True`` if it's the root resource, which have no parent. ``False`` otherwise.
    args : list, or None
        Arguments (list of subclasses of ``Arg``) to apply to the attribute represented by this
        resource. If not ``None``, the argument is assumed to be callable.
    filters : list
        List of ``Filter``. Each filter will be applied to the result of the previous one (the first
        filter being applied to the result of the attribute represented by the name of the
        resource)
    parent : Resource, or None
        Back reference to the parent resource. ``None`` if it's the root resource.

    """

    __slots__ = (
        'name',
        'entry_name',
        'is_root',
        'args',
        'filters',
        'parent',
    )

    def __init__(self, name, entry_name=None, args=None, filters=None, is_root=False):
        """Save attributes and set ``self`` as parent for the given filters.

        See the definition of the attributes on the class for more information about
        the arguments.

        Arguments
        ---------
        name : string
        entry_name : string, optional, default to ``name``
        args : list, optional, default to ``None``
        filters : list, optional, default to ``[]``
        is_root : boolean, optional, default to ``False``

        Notes:
        -----
        The only mandatory argument is ``name``.

        """

        super().__init__(args=args)

        self.name = name
        self.entry_name = entry_name or name
        self.is_root = is_root
        self.filters = filters or []

        self.parent = None

        for filter_ in self.filters:
            filter_.set_parent(self)

    def __repr__(self):
        """Returns a visual representation of a resource.

        Returns
        -------
        str
            The string representation of the resource.

        Example
        -------

        >>> Resource(name='foo', entry_name='bar', args=[
        ...     PosArg(1),
        ...     NamedArg('a', '=', 2),
        ... ], filters=[
        ...     Filter('filter', args=[
        ...         PosArg(3)
        ...     ])
        ... ], is_root=True)
        <Resource[bar] foo(1, a=2).filter(3) />

        """

        name = ' ' + self.name if self.filters or self.args or self.name != self.entry_name else ''
        result = '%(indent)s<%(cls)s[%(entry_name)s]%(name)s%(args)s%(filters)s />' % {
            'cls': self.__class__.__name__,
            'entry_name': self.entry_name,
            'name': '%s' % name,
            'args': '' if self.args is None else '(%s)' % ', '.join(map(str, self.args)),
            'filters': ''.join(map(str, self.filters)) if self.filters else '',
            'indent': '  ' * self.get_level()
        }
        return result

    def set_parent(self, parent):
        """Set the given parent as the parent resource."""

        self.parent = parent

    def get_level(self):
        """Return the level in the resources hierarchy. Mainly used for display.

        Returns
        -------
        int
            The level in the hierarchy, ``0`` for the root level, one more for each level.

        """

        if self.parent:
            return self.parent.get_level() + 1
        return 0


class Field(Resource):
    """A simple attribute to retrieve from a value (with or without filters."""

    pass


class MultiResources(Resource):
    """Base class for multi resources: get many attributes for one resource.

    It simply add a ``resources`` attributes to the base ``Resource`` class.
    Each sub-resource is an attribute of the main attribute.

    For example, the main attribute could be a date, and the sub-resources could
    be a list of ``Field`` resources: "day", "month", and "year".

    Attributes
    ----------
    resources : list
        List of subclasses of ``Resource``.

    """

    def __init__(self, name, entry_name=None, args=None, filters=None, is_root=False,
                 resources=None):
        """Save attributes and set ``self`` as parent for the given resources.

        See the definition of the attributes on the class for more information about
        the arguments.

        Arguments
        ---------
        name : string
        entry_name : string, optional, default to ``name``
        args : list, optional, default to ``None``
        filters : list, optional, default to ``[]``
        is_root : boolean, optional, default to ``False``
        resources : list, optional, default to ``[]``

        Notes:
        -----
        The only mandatory argument is ``name``.

        """

        super().__init__(name, entry_name, args, filters, is_root)

        self.resources = resources or []
        for resource in self.resources:
            resource.set_parent(self)

    def __repr__(self):
        """Returns a visual representation of a multi-resource.

        Returns
        -------
        str
            The string representation of the resource.

        Notes
        -----
        It simply transform the representation of the base resource to insert sub-resources in it,
        to have nested resources. Each subresource is indented depending of its level.

        Example
        -------

        >>> MultiResources('foo', resources=[
        ...     Field('bar'),
        ...     MultiResources('baz', resources=[
        ...         Field('qux')
        ...     ])
        ... ])
        <MultiResources[foo]>
          <Field[bar] />
          <MultiResources[baz]>
            <Field[qux] />
          </MultiResources[baz]>
        </MultiResources[foo]>

        """

        parent_repr = super().__repr__()

        if self.resources:
            return ('%(start)s\n'
                    '%(sub)s\n'
                    '%(indent)s</%(cls)s[%(entry_name)s]>') % {
                'start': parent_repr[:-3] + '>',
                'sub': '\n'.join(map(str, self.resources)),
                'cls': self.__class__.__name__,
                'entry_name': self.entry_name,
                'indent': '  ' * self.get_level(),
            }
        else:
            return parent_repr


class List(MultiResources):
    """A ``MultiResources`` subclass to represent list of values."""
    pass


class Object(MultiResources):
    """A ``MultiResources`` subclass to represent a value as dict of sub-attributes."""
    pass


class Filter(WithArgsMixin):
    """A filter is simply an attribute to call from a previous value.

    This previous value could be a previous filter, or the main value got from the resource.

    Attributes
    ----------
    name : string
        The name of the filter is the name of the attribute to get form a value.
    args : list or None
        List of arguments to pass to the attribute if callable. If ``None``, the attribute is
        assumed not to be callable.
    parent : Resource
        The ``Resource`` subclass instance having this filter.

    """
    __slots__ = (
        'name',
        'args',
        'parent',
    )

    def __init__(self, name, args=None):
        """Save attributes.

        See the definition of the attributes on the class for more information about
        the arguments.

        Arguments
        ---------
        name : string
        args : list, optional, default to ``None``

        Notes:
        -----
        The only mandatory argument is ``name``.

        """

        super().__init__(args=args)

        self.name = name
        self.parent = None

    def __repr__(self):
        """Returns a visual representation of a filter.

        Returns
        -------
        str
            The string representation of the filter.

        Example
        -------

        >>> Filter('foo')
        .foo
        >>> Filter('foo', args=[
        ...     PosArg(1),
        ...     NamedArg('a', '=', 2)
        ... ])
        .foo(1, a=2)

        """

        result = '.%(name)s' + ('' if self.args is None else '(%(args)s)')
        return result % {
            'name': self.name,
            'args': ', '.join(map(str, self.args)) if self.args else '',
        }

    def set_parent(self, parent):
        """Set the given parent as the parent resource."""
        self.parent = parent


class Arg:
    """Base class for resource or filter arguments.

    Attributes
    ----------
    arg : string
        The name of the argument.
    type : string
        The operator for this argument. Currently ignored in the rest of the ``dataql`` library
        (as is it is always "=").
    value : string, number, ``False``, ``True`` or ``None``
        The value of the argument.

    """
    __slots__ = (
        'arg',
        'type',
        'value',
        'parent',
    )

    def __init__(self, arg, arg_type, value):
        """Save attributes.

        See the definition of the attributes on the class for more information about
        the arguments.

        Arguments
        ---------
        arg : string
        arg_type : string
        value : string, number, ``False``, ``True`` or ``None``

        """

        self.arg = arg
        self.type = arg_type
        self.value = value

        self.parent = None

    def __repr__(self):
        """Returns a visual representation of a filter.

        Returns
        -------
        str
            The string representation of the filter.

        Example
        -------

        >>> Arg('foo', '=', 1)
        foo=1
        >>> Arg(None, None, 2)
        2

        """

        if self.is_named:
            result = '%(arg)s%(type)s%(value)s'
        else:
            result = '%(value)s'
        if isinstance(self.value, str):
            value = '"%s"' % (self.value.replace('"', '\\"'))
        else:
            value = self.value
        return result % {
            'arg': self.arg,
            'type': self.type,
            'value': value,
        }

    def set_parent(self, parent):
        """Set the given parent as the parent resource."""
        self.parent = parent

    @property
    def is_named(self):
        """Property telling if the argument is named or not.

        Example
        -------
        >>> Arg('foo', '=', 1).is_named
        True
        >>> Arg(None, None, 2).is_named
        False

        """

        return self.type is not None


class PosArg(Arg):
    """Positioned argument. It has no name and no type."""

    def __init__(self, value):
        super().__init__(arg=None, arg_type=None, value=value)


class NamedArg(Arg):
    """Named argument. It has a name and a type."""
    pass
