"""``resources`` module of ``dataql.solvers``.

This module holds the base solvers for filters:
- ``FilterSolver`` for ``Filter``
- ``SliceSolver`` for ``SlicingFilter``

Notes
-----
When we talk about "filters", we talk about subclasses of ``dataql.resources.BaseFilter``.

"""

from abc import abstractmethod, ABCMeta

from dataql.resources import Filter, SliceFilter


class Solver(metaclass=ABCMeta):
    """Base class for all filter solvers.

    The main entry point of a solver is the ``solve`` method, which must be defined
    for every solver.

    Attributes
    ----------
    solvable_filters : tuple (class attribute)
        Holds the filter classes (subclasses of ``dataql.resources.BaseFilter``) that can be
        solved by this solver.
        Must be defined in each sub-classes.
    registry : dataql.solvers.registry.Registry
        The registry that instantiated this solver.

    """

    solvable_filters = ()

    def __init__(self, registry):
        """Init the solver.

        Arguments
        ---------
        registry : dataql.solvers.registry.Registry
            The registry to use to get ``Source`` objects if needed.

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
        ...     def solve(self, value, filter): return value
        >>> MySolver(registry)
        <MySolver>

        """

        return '<%s>' % self.__class__.__name__

    @abstractmethod
    def solve(self, value, filter_):
        """Solve a filter with a value.

        Arguments
        ---------
        value : ?
            A value to solve in combination with the given filter.
        filter_ : dataql.resource.BaseFilter
            An instance of a subclass of ``BaseFilter`` to solve with the given value.

        Returns
        -------
        (depends on the implementation of the ``solve`` method)

        Raises
        ------
        CannotSolve
            If a solver accepts to solve a filter but cannot finally solve it.
            Allows ``Registry.solve_filter`` to use the next available solver.

        Notes
        -----
        This method must be defined in each subclass.

        """

        raise NotImplementedError()

    @classmethod
    def can_solve(cls, filter_):
        """Tells if the solver is able to resolve the given filter.

        Arguments
        ---------
        filter_ : subclass of dataql.resources.BaseFilter
            The subclass or ``BaseFilter`` to check if it is solvable by the current solver class.

        Returns
        -------
        boolean
            ``True`` if the current solver class can solve the given filter, ``False`` otherwise.

        Example
        -------

        >>> FilterSolver.solvable_filters
        (<class 'dataql.resources.Filter'>,)
        >>> FilterSolver.can_solve(Filter(name='foo'))
        True
        >>> SliceSolver.can_solve(Filter(name='foo'))
        False

        """

        for solvable_filter in cls.solvable_filters:
            if isinstance(filter_, solvable_filter):
                return True
        return False


class FilterSolver(Solver):
    """Solver aimed to solve the default filter which manage attributes or functions.

    This solver can only handle ``dataql.resources.Filter`` filters.

    Example
    -------

    >>> FilterSolver.solvable_filters
    (<class 'dataql.resources.Filter'>,)
    >>> FilterSolver.can_solve(Filter(name='foo'))
    True
    >>> FilterSolver.can_solve(SliceFilter(slice(1, 2, 3)))
    False

    """

    solvable_filters = (Filter, )

    def solve(self, value, filter_):
        """Returns the value of an attribute of the value, or the result of a call to a function.

        Arguments
        ---------
        value : ?
            A value to solve in combination with the given filter.
        filter_ : dataql.resource.Filter
            An instance of ``Filter`` to solve with the given value.

        Returns
        -------
        Depending on the source, the filter may ask for an attribute of the value, or for the
        result of a call to a standalone function taking the value as first argument.
        This method returns this attribute or result.

        Example
        -------

        >>> from dataql.solvers.registry import Registry
        >>> registry = Registry()
        >>> from datetime import date
        >>> registry.register(date, ['day', 'strftime'])
        >>> solver = FilterSolver(registry)
        >>> solver.solve(date(2015, 6, 1), Filter(name='day'))
        1
        >>> from dataql.resources import PosArg
        >>> solver.solve(date(2015, 6, 1), Filter(name='strftime', args=[PosArg('%F')]))
        '2015-06-01'

        """

        args, kwargs = filter_.get_args_and_kwargs()
        source = self.registry[value]
        return source.solve(value, filter_.name, args, kwargs)


class SliceSolver(Solver):
    """Solver aimed to get a slice or an entry of an iterable value.

    This solver can only handle ``dataql.resources.SliceFilter`` filters.

    Example
    -------

    >>> SliceSolver.solvable_filters
    (<class 'dataql.resources.SliceFilter'>,)
    >>> SliceSolver.can_solve(SliceFilter(slice(1, 2, 3)))
    True
    >>> SliceSolver.can_solve(Filter(name='foo'))
    False

    """

    solvable_filters = (SliceFilter, )

    def solve(self, value, filter_):
        """Get slice or entry defined by an index from the given value.

        Arguments
        ---------
        value : ?
            A value to solve in combination with the given filter.
        filter_ : dataql.resource.SliceFilter
            An instance of ``SliceFilter``to solve with the given value.

        Example
        -------

        >>> from dataql.solvers.registry import Registry
        >>> registry = Registry()
        >>> solver = SliceSolver(registry)
        >>> solver.solve([1, 2, 3], SliceFilter(1))
        2
        >>> solver.solve([1, 2, 3], SliceFilter(slice(1, None, None)))
        [2, 3]
        >>> solver.solve([1, 2, 3], SliceFilter(slice(0, 2, 2)))
        [1]
        >>> solver.solve([1, 2, 3], SliceFilter(4))

        """

        try:
            return value[filter_.slice or filter_.index]
        except IndexError:
            return None
