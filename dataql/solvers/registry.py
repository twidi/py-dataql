"""``registry`` module of ``dataql.solvers``.

A registry is the main entry point to solve dataql resources.

Simply create a registry, register classes with allowed attributes, some entry points,
and use the ``solve`` method to get the result value from a main value and a resource.

Example
-------

>>> from datetime import date
>>> registry = Registry()
>>> registry.register(date, ['strftime'])
>>> entry_points = EntryPoints(registry, today=date(2015, 6, 1))
>>> from dataql.resources import *
>>> resource = Field('today', filters=[Filter('strftime', args=[PosArg('%F')])])
>>> registry.solve(entry_points, resource)
'2015-06-01'

"""

from collections import Mapping

from dataql.solvers.base import AttributeSolver, ObjectSolver, ListSolver
from dataql.solvers.exceptions import CannotSolve
from dataql.utils import class_repr, isclass


class Attributes(frozenset):
    """A immutable set of attributes.

    If the set is created empty it will always return ``True`` when checking for
    the presence of an attribute, except if this attribute starts with ``_``.

    It allows to allow all public attributes of an instance to be accessible.

    If the set is created with elements, it will return ``True`` when checking for
    the presence of an attribute only if the attribute is in the set, even if it starts
    with ``_``.

    Attributes
    ----------

    contains_all : boolean
        ``True`` if no attributes where passed at create time, ``False`` otherwise.

    Example
    -------

    >>> a = Attributes(['foo', '_bar'])
    >>> 'foo' in a
    True
    >>> '_bar' in a
    True
    >>> 'baz' in a
    False
    >>> a.contains_all
    False
    >>> b = Attributes()
    >>> 'foo' in b
    True
    >>> '_bar' in b
    False
    >>> 'baz' in b
    True
    >>> b.contains_all
    True

    """

    def __new__(cls, *args):
        """Construct the set with the given attributes.

        Arguments
        ---------
        args : iterable
            A list (or other iterable) containing attributes to be in the set.
            Don't pass any argument to create a set that will always return ``True`` when
            checking for the presence of an attribute, except if it starts with ``_``.

        Returns
        -------
        Attributes
            The new created ``Attributes`` instance.

        """

        contains_all = False
        if not args or args == (None,):
            contains_all = True
            args = ([],)
        obj = super().__new__(cls, *args)
        obj.contains_all = contains_all
        return obj

    def __contains__(self, attribute):
        """Tells if the set contains the given attribute.

        Arguments
        ---------
        attribute : string
            The attribute to check for.

        Returns
        -------
        boolean
            ``True`` if the item is in the set (or, if the set was created empty, if it
            doesn't start with ``_``, ``False`` otherwise.

        """

        if not self.contains_all:
            return super().__contains__(attribute)
        if attribute.startswith('_'):
            return False
        return True


class BaseEntryPoints:
    """Base class for class created via ``EntryPoints``. May contains utilities in the future."""
    pass


def EntryPoints(registry, **kwargs):
    """Returns an instance of an object to use as entry point when calling ``registry.solve``.

    When calling ``registry.solve`` on a "root" resource, we don't have any value.
    This function will create a object to use as a first value and is used to specify which
    entry points are allowed at the first level of a dataql query.

    Example
    -------

    >>> from datetime import date
    >>> registry = Registry()
    >>> registry.register(date, ['strftime'])
    >>> entry_points = EntryPoints(registry, today=date(2015, 6, 1))
    >>> from dataql.resources import *
    >>> resource = Field('today', filters=[Filter('strftime', args=[PosArg('%F')])])
    >>> registry.solve(entry_points, resource)
    '2015-06-01'

    Notes
    -----
    The name of this function is intentionally made to resemble a class, as it returns an instance
    of a class named ``EntryPoints``.


    """

    klass = type('EntryPoints', (BaseEntryPoints, ), kwargs)
    registry.register(klass, kwargs.keys())
    return klass()


class Source:
    """A registered class, with its allowed attributes.

    Attributes
    ----------
    source : type
        The class for which we want to allow access to only some attributes.
    attributes : Attributes
        Instance of the ``Attributes`` class holding a set of names of allowed
        attributes for the source.
    allow_class : boolean
        If set to ``True``, the source apply not only to instances of the source class, but also to
        the class itself.
    allow_subclasses : boolean, default ``True``
        When ``True``, if an instance of a subclass is used without defined source, this
        source will be used.
    propagate_attributes : boolean, default ``True``
        When ``True``, all the attributes of this source will be propagated to subclasses of
        this source (except if the subclass has ``inherit_attributes`` set to ``False``.
        When ``False``, subclasses will have to declare their own attributes.
    inherit_attributes : boolean, default ``True``
        When ``True``, if the source class has a parent class in the registry, it will inherits
        its attributes if it has ``propagate_attributes`` set to ``True``.
        When ``False``, it has to declare its own attributes
    parent_sources : set
        If ``inherit_attributes`` is ``True``, this set will hold all the sources that are
        parent of the current one.

    Example
    -------

    >>> from datetime import date
    >>> d = date(2015, 6, 1)
    >>> s = Source(date, ['day', 'today'])
    >>> s.solve(d, 'day')
    1
    >>> s.solve(date, 'today')
    Traceback (most recent call last):
    Exception: Source `datetime.date` cannot solve `<class 'datetime.date'>`
    >>> s = Source(date, ['day', 'today'], allow_class=True)
    >>> s.solve(d, 'day')
    1
    >>> s.solve(date, 'today') == date.today()
    True

    """

    def __init__(self, source, attributes=None, allow_class=False, allow_subclasses=True,
                 propagate_attributes=True, inherit_attributes=True, parent_sources=None):
        """Initialize a source class with a list of allowed attributes.

        Arguments
        ---------
        source : type
            Must be a class for which we want to allow access to only the given attributes.
        attributes : iterable[str] / Attributes, optional
            A list (or other iterable) of string representing the names of the allowed
            attributes from the source.
            Can also be an ``Attributes`` instance.
            If not set, all attributes for this source will be allowed, except private ones
            (starting with ``_``)
        allow_class : boolean, default ``False``
            If set to ``True``, the source apply not only to instances of the source class, but
            also to the class itself.
        allow_subclasses : boolean, default ``True``
                When ``True``, if an instance of a subclass is used without defined source, this
                source will be used.
        propagate_attributes : boolean, default ``True``
            When ``True``, all the attributes of this source will be propagated to subclasses of
            this source (except if the subclass has ``inherit_attributes`` set to ``False``.
            When ``False``, subclasses will have to declare their own attributes.
        inherit_attributes : boolean, default ``True``
            When ``True``, if the source class has a parent class in the registry, it will inherits
            its attributes if it has ``propagate_attributes`` set to ``True``.
            When ``False``, it has to declare its own attributes
        parent_sources : set
            If ``inherit_attributes`` is ``True``, this set will hold all the sources that are
            parent of the current one.

        """
        if not isinstance(source, type):
            raise Exception('Source must be a class')
        self.source = source
        if not isinstance(attributes, Attributes):
            attributes = Attributes(attributes)
        self.attributes = attributes
        self.allow_class = allow_class
        self.allow_subclasses = allow_subclasses
        self.propagate_attributes = propagate_attributes
        self.inherit_attributes = inherit_attributes
        self.parent_sources = parent_sources or set()

    def __repr__(self):
        """String representation of a ``Source``.

        Returns
        -------
        str
            The string representation of the current ``Source`` instance.

        Example
        -------

        >>> from datetime import date
        >>> s = Source(date)
        >>> s
        <Source 'datetime.date'>

        """

        return "<Source '%s'>" % class_repr(self.source)

    def solve(self, value, attribute, args=None, kwargs=None):
        """Try to get the given attribute for the given value.

        If ``args`` or ``kwargs`` are passed, the attribute got from ``value`` must be callable.

        Arguments
        ---------
        value : object
            Instance of the class hold in ``self.source``
        attribute : str
            Name of the attribute to retrieve. Must be available through ``self.attributes``
        args : list, default ``None``
            If defined, list of non-named arguments that will be passed to the attribute if it's
            callable.
        kwargs : dict, default ``None``
            If defined, list of named arguments that will be passed to the attribute if it's
            callable.
        Returns
        -------
        Value of the ``attribute`` for the ``value`` instance.

        Raises
        ------
        Exception
            When the value is not an instance of the source class
        Exception
            When the attribute is not allowed
        TypeError
            If ``args`` or ``kwargs`` are passed and the result is not callable

        Example
        -------

        >>> from datetime import date
        >>> d = date(2015, 6, 1)
        >>> s = Source(date, ['day', 'strftime'])
        >>> s.solve(d, 'day')
        1
        >>> s.solve(d, 'strftime', ['%F'])
        '2015-06-01'
        >>> s.solve('a string', ['day'])
        Traceback (most recent call last):
        Exception: Source `datetime.date` cannot solve `a string`
        >>> s.solve(d, 'month')
        Traceback (most recent call last):
        Exception: `month` is not an allowed attribute for source `datetime.date`
        >>> s.solve(d, 'day', ['foo'])
        Traceback (most recent call last):
        TypeError: 'int' object is not callable

        """

        if not isinstance(value, self.source) and (
                not self.allow_class or value is not self.source):
            raise Exception('Source `%s` cannot solve `%s`' % (class_repr(self.source), value))

        if attribute not in self.attributes:
            found_in_parent = False
            for parent_source in self.parent_sources:
                if attribute in parent_source.attributes:
                    found_in_parent = True
                    break

            if not found_in_parent:
                raise Exception('`%s` is not an allowed attribute for source `%s`' % (
                    attribute, class_repr(self.source)))

        attr = getattr(value, attribute)

        # We make a call from the attribute in all cases if we have some arguments.
        # If we don't have arguments, we still check that the attribute is callable.
        # If yes and if it's not a class (it will always answer yes for a class), then
        # we call it.
        if args is not None or kwargs is not None or (not isclass(attr) and callable(attr)):
            attr = attr(*(args or []), **(kwargs or {}))

        return attr


class Registry(Mapping):
    """Registry of allowed classes with their allowed attributes.

    A registry holds a list ``Source`` instances, ie a list of class that are allowed to be used,
    and for each class, the list of attributes that can be accessed.

    A registry is a dict-like object so it can be iterated to get the list of sources, or used
    to get the ``Source`` instance from the source class.

    Then, when sources are registered, it is possible to use ``solve`` to solve a (value, resource)
    couple: one solver from the ``solvers`` class attribute will be used to find the solution.

    Attributes
    ----------
    solvers : tuple (class attribute)
        List of solver classes to use for solving a (value, resource) couple. The order is
        important because the first one that returns ``True`` to a call to its ``can_solve``
        method will be used.

    Example
    -------

    >>> from datetime import date, datetime
    >>> registry = Registry()
    >>> registry.register(date, ['day', 'month', 'year'])
    >>> registry.register(datetime, ['day', 'timestamp'])
    >>> list(registry)
    [<class 'datetime.date'>, <class 'datetime.datetime'>]
    >>> registry[date]
    <Source 'datetime.date'>
    >>> from dataql.resources import Field
    >>> registry.solve(date(2015, 6, 1), Field('day'))
    1

    """

    solvers = (AttributeSolver, ObjectSolver, ListSolver)

    def __init__(self):
        """Init the sources as an empty dictionnary."""

        self.sources = {}

    def register(self, source, attributes=None, allow_class=False, allow_subclasses=True,
                 propagate_attributes=True, inherit_attributes=True):
        """Register a source class with its attributes.

        Arguments
        ---------
        source : type
            Must be a class for which we want to allow access to only the given attributes.
        attributes : iterable[str] / Attributes, optional
            A list (or other iterable) of string representing the names of the allowed
            attributes from the source.
            Can also be an ``Attributes`` instance.
            If not set, all attributes for this source will be allowed, except private ones
            (starting with ``_``)
        allow_class : boolean, default ``False``
            If set to ``True``, the source apply not only to instances of the source class, but
            also to the class itself.
        allow_subclasses : boolean, default ``True``
                When ``True``, if an instance of a subclass is used without defined source, this
                source will be used.
        propagate_attributes : boolean, default ``True``
            When ``True``, all the attributes of this source will be propagated to subclasses of
            this source (except if the subclass has ``inherit_attributes`` set to ``False``.
            When ``False``, subclasses will have to declare their own attributes.
        inherit_attributes : boolean, default ``True``
            When ``True``, if the source class has a parent class in the registry, it will inherits
            its attributes if it has ``propagate_attributes`` set to ``True``.
            When ``False``, it has to declare its own attributes

        Raises
        ------
        Exception
            If the source class is already registered

        Example
        -------

        >>> from datetime import date
        >>> d = date(2015, 6, 1)
        >>> registry = Registry()
        >>> registry.register(date, ['day', 'today'])
        >>> registry[date].solve(d, 'day')
        1
        >>> registry[date].solve(date, 'today')
        Traceback (most recent call last):
        Exception: Source `datetime.date` cannot solve `<class 'datetime.date'>`
        >>> registry = Registry()
        >>> registry.register(date, ['day', 'today'], True)
        >>> s = Source(date, ['day', 'today'], allow_class=True)
        >>> registry[date].solve(d, 'day')
        1
        >>> registry[date].solve(date, 'today') == date.today()
        True

        """

        if source in self.sources:
            raise Exception('Source `%s` already in the registry' % source)

        # Inherit attributes from parent classes
        parent_sources = set()
        if inherit_attributes:
            bases = source.__bases__ if isinstance(source, type) else source.__class__.__bases__
            for klass in bases:
                if klass in self.sources and self.sources[klass].propagate_attributes:
                    parent_sources.add(self.sources[klass])

        self.sources[source] = Source(source, attributes, allow_class, allow_subclasses,
                                      propagate_attributes, inherit_attributes, parent_sources)

        # Propagate attributes to existing subclasses
        if propagate_attributes:
            for s in self.sources.values():
                if s.source != source and s.inherit_attributes and issubclass(s.source, source):
                    s.parent_source.add(self.sources[source])

    def __getitem__(self, source):
        """Get the ``Source`` instance for the given source class.

        Arguments
        ---------
        source : object
            The source to fetch in the registry dictionary.
            It may be an instance of a class, in which case its class will be used.
            It may be a subclass of a class in the registry, and if this one was registered
            with ``allow_subclasses`` set to ``True``, this class will be used.

        Returns
        -------
        Source
            The ``Source`` instance from the registry that matches the given source.

        Raises
        ------
        KeyError
            If the given source is not in the registry.

        Example
        -------

        >>> from datetime import date, datetime
        >>> registry = Registry()
        >>> registry.register(date, ['year', 'month', 'day'])
        >>> registry[date]
        <Source 'datetime.date'>
        >>> registry[date.today()]
        <Source 'datetime.date'>
        >>> registry[datetime]
        <Source 'datetime.date'>
        >>> registry = Registry()
        >>> registry.register(date, ['year', 'month', 'day'],allow_subclasses=False)
        >>> registry[datetime]
        Traceback (most recent call last):
        KeyError: <class 'datetime.datetime'>

        """

        # Get the class if the source is an instance.
        if not isinstance(source, type):
            source = source.__class__

        # Best case: we have the source itself, so we return it.
        if source in self.sources:
            return self.sources[source]

        # We don't have the source, we try to get one of its ancestors (only ancestors that
        # allow subclasses)
        for klass in source.mro()[1:]:  # "1:" to avoid using the source main class
            try:
                result = self.sources[klass]
            except KeyError:
                continue
            else:
                if result.allow_subclasses:
                    return result

        # Not found, return the default error of a ``__getitem__`` method.
        raise KeyError(source)

    def __iter__(self):
        """Iterate over the sources in this registry.

        As ``Registry`` is a dict-like object, iterating over it only returns keys, ie classes.
        To iterate over values, ie sources, use for example ``.values()`` or ``.items()``.

        Returns
        -------
        iterator
            An iterator over the keys (ie classes) in the registry.

        Example
        -------

        >>> registry = Registry()
        >>> from datetime import date, datetime
        >>> registry.register(date, ['year', 'month', 'day'])
        >>> registry.register(datetime, ['day', 'timestamp'])
        >>> for klass in registry: print(klass)
        <class 'datetime.date'>
        <class 'datetime.datetime'>
        >>> for klass in registry.keys(): print(klass)
        <class 'datetime.date'>
        <class 'datetime.datetime'>
        >>> for source in registry.values(): print(source)
        <Source 'datetime.date'>
        <Source 'datetime.datetime'>
        >>> for klass, source in registry.items(): print('%s : %s' % (klass, source))
        <class 'datetime.date'> : <Source 'datetime.date'>
        <class 'datetime.datetime'> : <Source 'datetime.datetime'>

        """

        return iter(self.sources)

    def __len__(self):
        """Return the number of sources in this registry.

        Example
        -------
        >>> registry = Registry()
        >>> from datetime import date, datetime
        >>> registry.register(date, ['year', 'month', 'day'])
        >>> registry.register(datetime, ['day', 'timestamp'])
        >>> len(registry)
        2

        """

        return len(self.sources)

    def get_solvers_classes(self, resource):
        """Returns the solver classes that can solve the given resource.

        Arguments
        ---------
        resource : Resource
            An instance of a subclass of ``dataql.resources.Resource`` for which we want
            to get the solver classes that can solve it.

        Returns
        -------
        list
            The list of solver classes that can solve the given resource.

        Raises
        ------
        Exception
            When no solver is able to solve the given resource.

        Example
        -------

        >>> from dataql.resources import Field, List
        >>> registry = Registry()
        >>> registry.get_solvers_classes(Field(name='foo'))
        [<class 'dataql.solvers.base.AttributeSolver'>]
        >>> registry.get_solvers_classes(List(name='foo'))
        [<class 'dataql.solvers.base.ListSolver'>]
        >>> registry.get_solvers_classes(None)
        Traceback (most recent call last):
        Exception: No solver found for `builtins.NoneType`

        """

        solvers = [s for s in self.solvers if s.can_solve(resource)]
        if solvers:
            return solvers
        raise Exception('No solver found for `%s`' % class_repr(resource))

    def solve(self, value, resource):
        """Solve the given resource for the given value.

        The solving is done by the first solver class that returns ``True`` when calling its
         ``can_solve`` method for the given resource, and that doesn't raise a ``CannotSolve``
         exception.

        Arguments
        ---------
        value : ?
            A value to be solved with the given resource.
        resource : Resource
            An instance of a subclass of ``dataql.resources.Resource`` to be solved with the
            given value..

        Returns
        -------
        The solved result.

        Raises
        ------
        Exception
            If no solvers were able to solve the resource. This happen if a solver says that
            it can solve a resource (by returning ``True`` when calling its ``can_solve`` method,
            but raises a ``CannotSolve`` exception during solving.

        Example
        -------
        >>> from datetime import date
        >>> registry = Registry()
        >>> registry.register(date, ['day', 'month', 'year'])
        >>> from dataql.resources import Field, Object, List
        >>> registry.solve(date(2015, 6, 1), Field('day'))
        1

        # Create an object from which we'll want an object (``date``) and a list (``dates``)
        >>> obj = EntryPoints(registry,
        ...     date = date(2015, 6, 1),
        ...     dates = [date(2015, 6, 1), date(2015, 6, 2)],
        ... )

        >>> d = registry.solve(
        ...     obj,
        ...     Object('date', resources=[Field('day'), Field('month'), Field('year')])
        ... )
        >>> [(k, d[k]) for k in sorted(d)]
        [('day', 1), ('month', 6), ('year', 2015)]

        >>> ds = list(registry.solve(
        ...     obj,
        ...     List('dates', resources=[Field('day'), Field('month'), Field('year')])
        ... ))
        >>> [[(k, d[k]) for k in sorted(d)] for d in ds]
        [[('day', 1), ('month', 6), ('year', 2015)], [('day', 2), ('month', 6), ('year', 2015)]]

        """

        solvers_classes = self.get_solvers_classes(resource)
        for solver_class in solvers_classes:
            try:
                solver = solver_class(self, value)
                return solver.solve_resource(value, resource)
            except CannotSolve:
                continue
        raise Exception('Solver(s) for `%s` found but no one able to solve it' %
                        class_repr(resource))
