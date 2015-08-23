"""``resources`` module of ``dataql.solvers``.

This module holds the base solvers for resources:
- ``AttributeSolver`` for ``Field``
- ``ObjectsSolver`` for ``Object``
- ``ListSolver`` for ``List``

Notes
-----
When we talk about "resources", we talk about subclasses of ``dataql.resources.Resource``.

"""

from abc import abstractmethod, ABCMeta
from collections import Iterable

from dataql.resources import Field, List, Object
from dataql.solvers.exceptions import NotIterable


class Solver(metaclass=ABCMeta):
    """Base class for all resource solvers.

    The main entry point of a solver is the ``solve`` method

    Attributes
    ----------
    solvable_resources : tuple (class attribute)
        Holds the resource classes (subclasses of ``dataql.resources.Resource``) that can be
        solved by this solver.
        Must be defined in each sub-classes.
    registry : dataql.solvers.registry.Registry
        The registry that instantiated this solver.

    Notes
    -----
    The ``solve`` method simply calls ``solve_value``, then ``coerce`` with the result.
    To change the behavior, simply override at least one of these two methods.

    """

    solvable_resources = ()

    def __init__(self, registry):
        """Init the solver.

        Arguments
        ---------
        registry : dataql.solvers.registry.Registry
            The registry to use to get the source and solve sub-resources if any.

        """

        self.registry = registry

    def __repr__(self):
        """String representation of a ``Solver`` instance.

        Returns
        -------
        str
            The string representation of the current ``Solver`` instance.

        Example
        -------

        >>> from dataql.solvers.registry import Registry
        >>> registry = Registry()
        >>> from datetime import date
        >>> registry.register(date, allow_class=True)
        >>> class MySolver(Solver):
        ...     def coerce(self, value, resource): return value
        >>> MySolver(registry)
        <MySolver>

        """

        return '<%s>' % self.__class__.__name__

    def solve(self, value, resource):
        """Solve a resource with a value.

        Arguments
        ---------
        value : ?
            A value to solve in combination with the given resource. The first filter of the
            resource will be applied on this value (next filters on the result of the previous
            filter).
        resource : dataql.resources.Resource
            An instance of a subclass of ``Resource`` to solve with the given value.

        Returns
        -------
        (depends on the implementation of the ``coerce`` method)

        Raises
        ------
        CannotSolve
            If a solver accepts to solve a resource but cannot finally solve it.
            Allows ``Registry.solve_resource`` to use the next available solver.

        Notes
        -----
        This method simply calls ``solve_value``, then ``coerce`` with the result.
        To change the behavior, simply override at least one of these two methods.

        """

        result = self.solve_value(value, resource)
        return self.coerce(result, resource)

    def solve_value(self, value, resource):
        """Solve a resource with a value, without coercing.

        Arguments
        ---------
        value : ?
            A value to solve in combination with the given resource. The first filter of the
            resource will be applied on this value (next filters on the result of the previous
            filter).
        resource : dataql.resources.Resource
            An instance of a subclass of ``Resource`` to solve with the given value.

        Returns
        -------
        The result of all filters applied on the value for the first filter, and result of the
        previous filter for next filters.

        Example
        -------

        >>> from dataql.solvers.registry import Registry
        >>> registry = Registry()
        >>> from datetime import date
        >>> registry.register(date, allow_class=True)
        >>> registry.register(str)
        >>> class MySolver(Solver):
        ...     def coerce(self, value, resource): return value
        >>> solver = MySolver(registry)
        >>> from dataql.resources import Filter, NamedArg, PosArg, SliceFilter
        >>> field = Field(None,
        ...     filters=[
        ...         Filter(name='fromtimestamp', args=[PosArg(1433109600)]),
        ...         Filter(name='replace', args=[NamedArg('year', '=', 2014)]),
        ...         Filter(name='strftime', args=[PosArg('%F')]),
        ...         Filter(name='replace', args=[PosArg('2014'), PosArg('2015')]),
        ...     ]
        ... )
        >>> solver.solve_value(date, field)
        '2015-06-01'
        >>> solver.solve_value(None, field)

        >>> d = {'foo': {'date': date(2015, 6, 1)}, 'bar': {'date': None}, 'baz': [{'date': None}]}
        >>> registry.register(dict)
        >>> solver.solve_value(d, Field(None, filters=[
        ...     Filter(name='foo'),
        ...     Filter(name='date'),
        ...     Filter(name='strftime', args=[PosArg('%F')]),
        ... ]))
        '2015-06-01'
        >>> solver.solve_value(d, Field(None, filters=[
        ...     Filter(name='bar'),
        ...     Filter(name='date'),
        ...     Filter(name='strftime', args=[PosArg('%F')]),
        ... ]))

        >>> solver.solve_value(d, Field(None, filters=[
        ...     Filter(name='baz'),
        ...     SliceFilter(0),
        ...     Filter(name='date'),
        ...     Filter(name='strftime', args=[PosArg('%F')]),
        ... ]))

        # Example of how to raise a ``CannotSolve`` exception.
        >>> from dataql.solvers.exceptions import CannotSolve
        >>> raise CannotSolve(solver, Field('fromtimestamp'), date)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        dataql...CannotSolve: Solver `<MySolver>` was not able to solve...`<Field[fromtimestamp]>`.

        """

        # The given value is the starting point on which we apply the first filter.
        result = value

        # Apply filters one by one on the previous result.
        if result is not None:
            for filter_ in resource.filters:
                result = self.registry.solve_filter(result, filter_)
                if result is None:
                    break

        return result

    @abstractmethod
    def coerce(self, value, resource):
        """Convert the value got after ``solve_value``.

        Must be implemented in subclasses.

        """

        raise NotImplementedError()

    @classmethod
    def can_solve(cls, resource):
        """Tells if the solver is able to resolve the given resource.

        Arguments
        ---------
        resource : subclass of ``dataql.resources.Resource``
            The resource to check if it is solvable by the current solver class

        Returns
        -------
        boolean
            ``True`` if the current solver class can solve the given resource, ``False`` otherwise.

        Example
        -------

        >>> AttributeSolver.solvable_resources
        (<class 'dataql.resources.Field'>,)
        >>> AttributeSolver.can_solve(Field('foo'))
        True
        >>> AttributeSolver.can_solve(Object('bar'))
        False

        """

        for solvable_resource in cls.solvable_resources:
            if isinstance(resource, solvable_resource):
                return True
        return False


class AttributeSolver(Solver):
    """Solver aimed to retrieve fields from values.

    This solver can only handle ``dataql.resources.Field`` resources.

    Attributes
    ----------
    solvable_resources : tuple (class attribute)
        Holds the resource classes (from ``dataql.resources``) that can be solved by this solver.

    Example
    -------

    >>> from dataql.solvers.registry import Registry
    >>> registry = Registry()
    >>> from datetime import date
    >>> registry.register(date)
    >>> solver = AttributeSolver(registry)
    >>> solver.solve(date(2015, 6, 1), Field('year'))
    2015

    """

    solvable_resources = (Field,)

    def coerce(self, value, resource):
        """Coerce the value to an acceptable one.

        Only these kinds of values are returned as is:
        - str
        - int
        - float
        - True
        - False
        - None

        For all others values, it will be coerced using ``self.coerce_default`` (with convert the
        value to a string in the default implementation).

        Arguments
        ---------
        value : ?
            The value to be coerced.
        resource : dataql.resources.Resource
            The ``Resource`` object used to obtain this value from the original one.

        Returns
        -------
        str | int | float | True | False | None
            The coerced value.

        Example
        -------

        >>> from dataql.solvers.registry import Registry
        >>> registry = Registry()
        >>> from datetime import date
        >>> registry.register(date)
        >>> solver = AttributeSolver(registry)
        >>> solver.coerce('foo', None)
        'foo'
        >>> solver.coerce(11, None)
        11
        >>> solver.coerce(1.1, None)
        1.1
        >>> solver.coerce(True, None)
        True
        >>> solver.coerce(False, None)
        False
        >>> solver.coerce(date(2015, 6, 1), None)
        '2015-06-01'
        >>> solver.coerce(None, None)

        """
        if value in (True, False, None):
            return value
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            return value
        return self.coerce_default(value, resource)

    def coerce_default(self, value, resource):
        """Coerce a value using a default converter, ``str()``.

        Arguments
        ---------
        value : ?
            The value to be coerced.
        resource : dataql.resources.Resource
            The ``Resource`` object used to obtain this value from the original one.

        Returns
        -------
        str
            The coerced value.

        Example
        -------

        >>> from dataql.solvers.registry import Registry
        >>> registry = Registry()
        >>> from datetime import date
        >>> registry.register(date)
        >>> solver = AttributeSolver(registry)
        >>> solver.coerce_default(date(2015, 6, 1), None)
        '2015-06-01'
        >>> solver.coerce_default(date, None)
        "<class 'datetime.date'>"

        """

        return str(value)


class ObjectSolver(Solver):
    """Solver aimed to retrieve many fields from values.

    This solver can only handle ``dataql.resources.Object`` resources.

    Example
    -------

        >>> from dataql.solvers.registry import Registry
        >>> registry = Registry()
        >>> from datetime import date
        >>> registry.register(date)

        # Create an object from which we'll want an object (``date``)
        >>> from dataql.solvers.registry import EntryPoints
        >>> obj = EntryPoints(registry,
        ...     date = date(2015, 6, 1),
        ... )

        >>> solver = ObjectSolver(registry)
        >>> d = solver.solve(
        ...     obj,
        ...     Object('date', resources=[Field('day'), Field('month'), Field('year')])
        ... )
        >>> [(k, d[k]) for k in sorted(d)]
        [('day', 1), ('month', 6), ('year', 2015)]

    """

    solvable_resources = (Object,)

    def coerce(self, value, resource):
        """Get a dict with attributes from ``value``.

        Arguments
        ---------
        value : ?
            The value to get some resources from.
        resource : dataql.resources.Object
            The ``Object`` object used to obtain this value from the original one.

        Returns
        -------
        dict
            A dictionary containing the wanted resources for the given value.
            Key are the ``name`` attributes of the resources, and the values are the solved values.

        """

        return {r.name: self.registry.solve_resource(value, r) for r in resource.resources}


class ListSolver(Solver):
    """Solver aimed to retrieve many fields from many values of the same type.

    This solver can only handle ``dataql.resources.List`` resources.

    Example
    -------

        >>> from dataql.solvers.registry import Registry
        >>> registry = Registry()
        >>> from datetime import date
        >>> registry.register(date)

        # Create an object from which we'll want a list (``dates``)
        >>> from dataql.solvers.registry import EntryPoints
        >>> obj = EntryPoints(registry,
        ...     dates = [date(2015, 6, 1), date(2015, 6, 2)],
        ...     date = date(2015, 6, 1),
        ... )

        >>> solver = ListSolver(registry)

        >>> from dataql.resources import Filter, PosArg
        >>> solver.solve(
        ...     obj,
        ...     List('dates', resources=[Field(None, [Filter('strftime', args=[PosArg('%F')])])])
        ... )
        ['2015-06-01', '2015-06-02']

        >>> solver.solve(
        ...     obj,
        ...     List('dates', resources=[Field('day'), Field('month'), Field('year')])
        ... )
        [[1, 6, 2015], [2, 6, 2015]]

        >>> from pprint import pprint  # will sort the dicts by keys
        >>> pprint(solver.solve(
        ...     obj,
        ...     List('dates', resources=[
        ...         Field(None, [Filter('strftime', args=[PosArg('%F')])]),
        ...         Object(None, resources=[Field('day'), Field('month'), Field('year')]),
        ...         ])
        ... ))
        [['2015-06-01', {'day': 1, 'month': 6, 'year': 2015}],
         ['2015-06-02', {'day': 2, 'month': 6, 'year': 2015}]]

        >>> pprint(solver.solve(
        ...     obj,
        ...     List('dates', resources=[
        ...         Object(None, resources=[Field('day'),Field('month'), Field('year')])
        ...     ])
        ... ))
        [{'day': 1, 'month': 6, 'year': 2015}, {'day': 2, 'month': 6, 'year': 2015}]

        >>> solver.solve(
        ...     obj,
        ...     List('date', resources=[Field('day'), Field('month'), Field('year')])
        ... ) # doctest: +ELLIPSIS
        Traceback (most recent call last):
        dataql.solvers.exceptions.NotIterable: ...


    """

    solvable_resources = (List,)

    def coerce(self, value, resource):
        """Convert a list of objects in a list of dicts.

        Arguments
        ---------
        value : iterable
            The list (or other iterable) to get values to get some resources from.
        resource : dataql.resources.List
            The ``List`` object used to obtain this value from the original one.

        Returns
        -------
        list
            A list with one entry for each iteration get from ``value``.
            If the ``resource`` has only one sub-resource, each entry in the result list will
            be the result for the subresource for each iteration.
            If the ``resource`` has more that one sub-resource, each entry in the result list will
            be another list with an entry for each subresource for the current iteration.

        Raises
        ------
        dataql.solvers.exceptions.NotIterable
            When the value is not iterable.

        """

        if not isinstance(value, Iterable):
            raise NotIterable(resource, self.registry[value])

        # Case #1: we only have one sub-resource, so we return a list with this item for
        # each iteration
        if len(resource.resources) == 1:
            res = resource.resources[0]
            return [self.registry.solve_resource(v, res) for v in value]

        # Case #2: we have many sub-resources, we return a list with, for each iteration, a
        # list with all entries
        return [
            [self.registry.solve_resource(v, res) for res in resource.resources]
            for v in value
        ]
