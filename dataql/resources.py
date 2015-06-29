"""``resources`` module of ``dataql``.

It provides the different classes that are used to store a usable structure from a query
parsed by a dataql parser.

We have three resources. Each one has a name, and filters (subclasses of ``BaseFilter``).

The three resources are:

- ``Field`` : a simple field. A parser may cast it into a simple value (string, number, null,
              false or true)
- ``Object`` : the value is an object from which we want some fields.
- ``List`` : the value is an iterable, and for each entry we want some fields

The name is used as the entry-point for the output, and filters are used to retrieve data from
the value (the first filter uses the main value, and each next filter use the result of the
previous filter).
A ``Filter`` may be an attribute, that may be callable (which can have arguments if any
(``NamedArg`` and ``PosArg``), but it could also be a standalone function (taking the value
as first argument, and then the other arguments)
A ``SliceFilter`` allows to retrieve one or more entries of an iterable.
When all filters are applied, the final value is casted (number, string... for ``Field``,
dictionary for ``Object`` and list for ``List``).


To use subclasses of the classes defined here, they must be set on the parser:

    class MyList(List):
        pass

    class MyParser(BaseParser):
        List = MyList

"""

__all__ = ('Field', 'List', 'Object', 'Filter', 'NamedArg', 'PosArg')

from abc import ABCMeta


class Resource(metaclass=ABCMeta):
    """Base class for all resource classes.

    A resource is a name and some filters.
    The name will be used as the entry point in the output, and the filters will be
    applied to a value (each filter applied to the result of the previous filter)

    Attributes
    ----------
    name : string
        The name of the resource on the output.
    is_root : boolean
        ``True`` if it's the root resource, which have no parent. ``False`` otherwise.
    filters : list, optional
        List of instances of subclasses of ``BaseFilter`` .
        Each filter will be applied to the result of the previous one (the first filter being
        applied to the value passed to the solver) If no filter was given on ``__init__``, a
        filter will be added with the name of the resource (to fetch this name as an attribute
        during solving)
    parent : Resource, or None
        Back reference to the parent resource. ``None`` if it's the root resource.

    """

    __slots__ = (
        'name',
        'is_root',
        'filters',
        'parent',
    )

    def __init__(self, name, filters=None, is_root=False):
        """Save attributes and set ``self`` as parent for the given filters.

        See the definition of the attributes on the class for more information about
        the arguments.

        Arguments
        ---------
        name : string
        filters : list or None
        is_root : boolean, optional, default to ``False``

        """

        self.name = name
        self.is_root = is_root
        self.filters = filters or []

        self.parent = None

        if not self.filters and self.name:
            self.filters = [Filter(name=self.name)]

        for filter_ in self.filters:
            filter_.set_parent(self)

    def __repr__(self):
        """String representation of a ``Resource`` instance.

        Returns
        -------
        str
            The string representation of the current ``Resource`` instance.

        Example
        -------

        >>> Resource(name='bar', filters=[
        ...     Filter('foo', args=[
        ...         PosArg(1),
        ...         NamedArg('a', '=', 2)
        ...     ]),
        ...     Filter('filter', args=[
        ...         PosArg(3)
        ...     ])
        ... ], is_root=True)
        <Resource[bar] .foo(1, a=2).filter(3) />

        """

        filters = ''
        if len(self.filters) > 1 or self.filters and (
                self.filters[0].name != self.name or self.filters[0].args):
            filters = ' ' + ''.join(map(str, self.filters))

        result = '%(indent)s<%(cls)s%(name)s%(filters)s />' % {
            'cls': self.__class__.__name__,
            'name': ('[%s]' % self.name) if self.name else '',
            'filters': filters,
            'indent': '  ' * self.get_level(),
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
    """A simple field to retrieve from a value by using its filters."""

    pass


class MultiResources(Resource, metaclass=ABCMeta):
    """Base class for multi resources: get many fields for one resource.

    It simply add a ``resources`` attributes to the base ``Resource`` class.
    Each sub-resource is an field to retrieve of the main value using some filters.

    For example, the main attribute could be a date, and the sub-resources could
    be a list of ``Field`` resources: "day", "month", and "year".

    Attributes
    ----------
    resources : list
        List of subclasses of ``Resource``.

    """

    def __init__(self, name, filters=None, is_root=False, resources=None):
        """Save attributes and set ``self`` as parent for the given resources.

        See the definition of the attributes on the class for more information about
        the arguments.

        Arguments
        ---------
        name : string
        filters : list, optional
        is_root : boolean, optional, default to ``False``
        resources : list, optional, default to ``[]``

        """

        super().__init__(name, filters, is_root)

        self.resources = resources or []
        for resource in self.resources:
            resource.set_parent(self)

    def __repr__(self):
        """String representation of a ``MultiResources`` instance.

        Returns
        -------
        str
            The string representation of the current ``MultiResources`` instance.

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
            return (
                '%(start)s\n'
                '%(sub)s\n'
                '%(indent)s</%(cls)s%(name)s>'
            ) % {
                'start': parent_repr[:-3] + '>',
                'sub': '\n'.join(map(str, self.resources)),
                'cls': self.__class__.__name__,
                'name': ('[%s]' % self.name) if self.name else '',
                'indent': '  ' * self.get_level(),
            }
        else:
            return parent_repr


class List(MultiResources):
    """A ``MultiResources`` subclass to represent list of values."""
    pass


class Object(MultiResources):
    """A ``MultiResources`` subclass to represent a value as dict of sub-fields."""
    pass


class BaseFilter(metaclass=ABCMeta):
    """A filter is "something" to apply to a value to get another value.

    This base class is to be used to all filters.

    Attributes
    ----------
    parent : Resource
        The ``Resource`` subclass instance having this filter.

    """

    __slots__ = (
        'parent',
    )

    def __init__(self):
        """Set the ``parent`` attribute to ``None``."""
        self.parent = None

    def set_parent(self, parent):
        """Set the given parent as the parent resource."""
        self.parent = parent


class Filter(BaseFilter):
    """A filter is simply an attribute to call from a previous value, or a standalone function.

    This previous value could be a previous filter, or the main value got from the resource.

    Attributes
    ----------
    name : string
        The name of the filter is the name of the attribute to get from a value (or the function
        to use). Must be allowed by the ``Source`` object related to the value.
    args : list, optional
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

        """

        super().__init__()

        self.name = name

        self.args = args
        if self.args:
            for arg in self.args:
                arg.set_parent(self)

    def __repr__(self):
        """String representation of a ``Filter`` instance.

        Returns
        -------
        str
            The string representation of the current ``Filter`` instance.

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

    def get_args_and_kwargs(self):
        """Return a list and a dict usable as ``*args, **kwargs`` to pass to a callable."

        If the entity is known to not accept arguments (``self.args`` is ``None``), then this
        method returns ``None`` for both args and kwargs.

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


class SliceFilter(BaseFilter):
    """A slice used as a filter to get one or many entries from an iterable.

    Only one of the ``slice`` and ``index`` attributes are defined for a ``SliceFilter`` object.

    Attributes
    ----------
    slice : slice
        A ``slice`` object with its attributes: ``start``, ``stop``, ``step``.
    index : int
        An integer for a simple item retrieval
    parent : Resource
        The ``Resource`` subclass instance having this slice-filter.

    """

    __slots__ = (
        'slice',
        'index',
        'parent'
    )

    def __init__(self, slice_info):
        """Save attributes.

        Arguments
        ---------
        slice_info : slice or number
            If a ``slice``, value will be saved in ``self.slice``, otherwise in ``self.index``.

        """

        super().__init__()

        if isinstance(slice_info, slice):
            self.slice, self.index = slice_info, None
        else:
            self.slice, self.index = None, slice_info

    def __repr__(self):
        """String representation of a ``SliceFilter`` instance.

        Returns
        -------
        str
            The string representation of the current ``SliceFilter`` instance.

        Example
        -------

        >>> SliceFilter(1)
        [1]
        >>> SliceFilter(slice(None, None, None))
        [:]
        >>> SliceFilter(slice(1, None, None))
        [1:]
        >>> SliceFilter(slice(None, 2, None))
        [:2]
        >>> SliceFilter(slice(1, 2, None))
        [1:2]
        >>> SliceFilter(slice(None, None, 3))
        [::3]
        >>> SliceFilter(slice(None, 2, 3))
        [:2:3]
        >>> SliceFilter(slice(1, None, 3))
        [1::3]
        >>> SliceFilter(slice(1, 2, 3))
        [1:2:3]

        """

        # Manage simple index.
        if self.index is not None:
            return '[%s]' % self.index

        # Manage ``slice`` object.
        if self.slice.step is None:
            if self.slice.stop is None:
                return '[:]' if self.slice.start is None else '[%s:]' % self.slice.start
            else:
                return '[%s:%s]' % (
                    '' if self.slice.start is None else self.slice.start,
                    self.slice.stop
                )
        else:
            return '[%s:%s:%s]' % (
                '' if self.slice.start is None else self.slice.start,
                '' if self.slice.stop is None else self.slice.stop,
                self.slice.step,
            )


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
        """String representation of an ``Arg`` instance.

        Returns
        -------
        str
            The string representation of the current ``Arg`` instance.

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
