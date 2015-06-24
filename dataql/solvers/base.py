"""``base`` module of ``dataql.solvers``.

This module holds the base solvers, one for simple attributes (``AttributeSolver``, one for
objects (``ObjectSolver``), and one for lists (``ListSolver``).

Notes
-----
When we talk about "resources", we talk about instances of classes defined in ``dataql.resources``
(or inherited classes of course)

"""

from abc import abstractmethod, ABCMeta
from collections import Iterable

from dataql.resources import Field, List, Object
from dataql.solvers.exceptions import NotIterable


class Solver(metaclass=ABCMeta):
    """Base class for all solvers.

    The main entry point of a solver is the ``solve`` method, which must be defined
    for every solver.

    Attributes
    ----------
    solvable_resources : tuple (class attribute)
        Holds the resource classes (from ``dataql.resources``) that can be solved by this solver.
        Must be defined in each sub-classes.
    registry : dataql.solvers.registry.Registry
        The registry that instantiated this solver.

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
        ...     def cast(self, value, resource): return value
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
        resource : Resource
            An instance of a subclass of ``dataql.resources.Resource`` to solve with the given
            value.

        Returns
        -------
        (depends on the implementation of the ``cast`` method)

        Raises
        ------
        CannotSolve
            If a solver accepts to solve a resource but cannot finally solve it.
            Allows ``Registry.solve`` to use the next available solver.

        Notes
        -----
        This method simply calls ``solve_value``, then ``cast`` with the result.
        To change the behavior, simply override one of these two methods.

        """

        result = self.solve_value(value, resource)
        return self.cast(result, resource)

    def solve_value(self, value, resource):
        """Solve a resource with a value, without casting.

        Arguments
        ---------
        value : ?
            A value to solve in combination with the given resource. The first filter of the
            resource will be applied on this value (next filters on the result of the previous
            filter).
        resource : Resource
            An instance of a subclass of ``dataql.resources.Resource`` to solve with the given
            value.

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
        >>> registry.register(str, allow_class=True)
        >>> class MySolver(Solver):
        ...     def cast(self, value, resource): return value
        >>> solver = MySolver(registry)
        >>> from dataql.resources import Filter, NamedArg, PosArg
        >>> solver.solve_value(date, Field('fromtimestamp',
        ...     filters=[
        ...         Filter(name='fromtimestamp', args=[PosArg(1433109600)]),
        ...         Filter(name='replace', args=[NamedArg('year', '=', 2014)]),
        ...         Filter(name='strftime', args=[PosArg('%F')]),
        ...         Filter(name='replace', args=[PosArg('2014'), PosArg('2015')]),
        ...     ]
        ... ))
        '2015-06-01'

        # Example of how to raise a ``CannotSolve`` exception.
        >>> from dataql.solvers.exceptions import CannotSolve
        >>> raise CannotSolve(solver, Field('fromtimestamp'), date)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        dataql...CannotSolve: Solver `<MySolver>` was not able to solve...`<Field[fromtimestamp]>`.

        """

        # The given value is the starting point on which we apply the first filter.
        result = value

        # Apply filters one by one on the previous result.
        for filter_ in resource.filters:
            args, kwargs = filter_.get_args_and_kwargs()
            source = self.registry[result]
            result = source.solve(result, filter_.name, args, kwargs)

        return result

    @abstractmethod
    def cast(self, value, resource):
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

    def cast(self, value, resource):
        """Cast the value to an acceptable one.

        Only these kinds of values are returned as is:
        - str
        - int
        - float
        - True
        - False
        - None

        For all others values, it will be casted using ``self.cast_default`` (with convert the
        value to a string in the default implementation).

        Arguments
        ---------
        value : ?
            The value to be casted.
        resource : dataql.resources.Resource
            The ``Resource`` object used to obtain this value from the original one.

        Returns
        -------
        str | int | float | True | False | None
            The casted value.

        Example
        -------

        >>> from dataql.solvers.registry import Registry
        >>> registry = Registry()
        >>> from datetime import date
        >>> registry.register(date)
        >>> solver = AttributeSolver(registry)
        >>> solver.cast('foo', None)
        'foo'
        >>> solver.cast(11, None)
        11
        >>> solver.cast(1.1, None)
        1.1
        >>> solver.cast(True, None)
        True
        >>> solver.cast(False, None)
        False
        >>> solver.cast(date(2015, 6, 1), None)
        '2015-06-01'
        >>> solver.cast(None, None)

        """
        if value in (True, False, None):
            return value
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            return value
        return self.cast_default(value, resource)

    def cast_default(self, value, resource):
        """Cast a value using a default converter, ``str()``.

        Arguments
        ---------
        value : ?
            The value to be casted.
        resource : dataql.resources.Resource
            The ``Resource`` object used to obtain this value from the original one.

        Returns
        -------
        str
            The casted value.

        Example
        -------

        >>> from dataql.solvers.registry import Registry
        >>> registry = Registry()
        >>> from datetime import date
        >>> registry.register(date)
        >>> solver = AttributeSolver(registry)
        >>> solver.cast_default(date(2015, 6, 1), None)
        '2015-06-01'
        >>> solver.cast_default(date, None)
        "<class 'datetime.date'>"

        """

        return str(value)


class MultiResourcesBaseSolver(Solver, metaclass=ABCMeta):
    """A base class for solver for resources with sub-resources.

    Notes
    -----
    This base class simply provides a ``solve_subresources`` method to return a dict containing
    each solved resources.

    """

    def solve_subresources(self, value, resources):
        """Solve many resources from a value.

        Arguments
        ---------
        value : ?
            The value to get some resources from.
        resources : iterable[dataql.resource.Resource]
            A list (or other iterable) of resources (instances of ``dataql.resource.Resource``
            subclasses).

        Returns
        -------
        dict
            A dictionary containing the wanted resources for the given value.
            Key are the ``name`` attributes of the resources, and the values are the solved values.

        Example
        -------
        >>> from dataql.solvers.registry import Registry
        >>> registry = Registry()
        >>> from datetime import date
        >>> registry.register(date)
        >>> solver = ObjectSolver(registry)
        >>> d = solver.solve_subresources(date(2015, 6, 1), [
        ... Field('day'), Field('month'), Field('year')])
        >>> [(k, d[k]) for k in sorted(d)]
        [('day', 1), ('month', 6), ('year', 2015)]

        """

        return {r.name: self.registry.solve(value, r) for r in resources}


class ObjectSolver(MultiResourcesBaseSolver):
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

    def cast(self, value, resource):
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

        return self.solve_subresources(value, resource.resources)


class ListSolver(MultiResourcesBaseSolver):
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

        >>> ds = list(solver.solve(
        ...     obj,
        ...     List('dates', resources=[Field('day'), Field('month'), Field('year')])
        ... ))
        >>> [[(k, d[k]) for k in sorted(d)] for d in ds]
        [[('day', 1), ('month', 6), ('year', 2015)], [('day', 2), ('month', 6), ('year', 2015)]]

        >>> ds = list(solver.solve(
        ...     obj,
        ...     List('date', resources=[Field('day'), Field('month'), Field('year')])
        ... )) # doctest: +ELLIPSIS
        Traceback (most recent call last):
        dataql.solvers.exceptions.NotIterable: ...


    """

    solvable_resources = (List,)

    def cast(self, value, resource):
        """Convert a list of objects in a list of dicts.

        Arguments
        ---------
        value : iterable
            The list (or other iterable) to get values to get some resources from.
        resource : dataql.resources.List
            The ``List`` object used to obtain this value from the original one.

        Returns
        -------
        list[dict]
            A list of dictionaries containing the wanted resources for the given values.
            Key are the ``name`` attributes of the resources, and the values are the solved values.

        Raises
        ------
        dataql.solvers.exceptions.NotIterable
            When the value is not iterable.

        """

        if not isinstance(value, Iterable):
            raise NotIterable(resource, self.registry[value])
        return [self.solve_subresources(entry, resource.resources) for entry in value]
