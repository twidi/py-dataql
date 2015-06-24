"""``exceptions`` module of ``dataql.solvers``.

It holds all the exception that may be raised by this module.

"""

from abc import ABCMeta

from dataql.exceptions import DataQLException
from dataql.utils import class_repr


__all__ = (
    'AlreadyRegistered',
    'AttributeNotFound',
    'CallableError',
    'CannotSolve',
    'InvalidSource',
    'NotIterable',
    'NotSolvable',
    'SolveFailure',
    'SolverNotFound',
    'SourceNotFound',
)


class SolversException(DataQLException, metaclass=ABCMeta):
    """Base for exceptions raised in the ``dataql.solvers`` module."""
    pass


class SolverObjectException(SolversException, metaclass=ABCMeta):
    """Base for exceptions raised by a ``Solver`` object."""
    pass


class CannotSolve(SolverObjectException):
    """Exception raised when a solver accepts to solve a resource but is not able to do it.

    This exception string exposes the name and class of the solver and the resource.

    Attributes
    ---------
    solver : dataql.solvers.base.Solver
        The ``Solver`` object that raised this exception.
    resource : dataql.resources.Resource
        The ``Resource`` object the solver was not able to solve.
    value : ?
        The value for which the solver was not able to solve the resource.

    """

    def __init__(self, solver, resource, value):
        self.solver = solver
        self.resource = resource
        self.value = value
        super().__init__(str(self))

    def __str__(self):
        return 'Solver `%s` was not able to solve resource `%s`.' % (
            self.solver,
            '<%s[%s]>' % (self.resource.__class__.__name__, self.resource.name)
        )


class AttributeSolverException(SolverObjectException, metaclass=ABCMeta):
    """Base for exceptions raised by a ``AttributeSolver`` object."""
    pass


class ObjectSolverException(SolverObjectException, metaclass=ABCMeta):
    """Base for exceptions raised by a ``ObjectSolver`` object."""
    pass


class ListSolverException(SolverObjectException, metaclass=ABCMeta):
    """Base for exceptions raised by a ``ListSolver`` object."""
    pass


class NotIterable(ListSolverException):
    """Exception raised by a ``ListSolver`` object if a resource is not iterable.

    The exception string exposes the name of the resource that is not iterable, and
    the class source from which the attribute was got.

    Attributes
    ----------
    resource : dataql.resources.Resource
        The resource that is not iterable (the attribute from ``source``).
    source : dataql.solvers.registry.Source
        The source object containing the non-iterable resource.

    """

    def __init__(self, resource, source):
        self.resource = resource
        self.source = source
        super().__init__(str(self))

    def __str__(self):
        return '`%s` from source `%s` is not iterable' % (
            self.resource.name,
            class_repr(self.source.source),
        )


class AttributeException(SolversException, metaclass=ABCMeta):
    """Base for exceptions raised by an ``Attribute`` or ``Attributes`` object."""
    pass


class AttributeNotFound(AttributeException, KeyError):
    """Exception raised when an attribute was not found.

    The exception string exposes the name of the not found attribute, and the source if
    available.

    Attributes
    ----------
    name : str
        The name of the attribute that couldn't be found.
    source : dataql.solvers.registry.Source, optional
        If set, the source from which the attribute was not found.

    """

    def __init__(self, name, source=None):
        self.name = name
        self.source = source
        super().__init__(str(self))

    def __str__(self):
        if self.source:
            return '`%s` is not an allowed attribute for `%s`' % (
                self.name,
                class_repr(self.source.source),
            )
        else:
            return '`%s` is not an allowed attribute' % (
                self.name,
            )


class CallableError(AttributeException):
    """Exception raised when an attribute/function was called, raising an exception.

    The exception string only exposes the name of the attribute and if their were arguments
    or not.

    Attributes
    ----------
    attribute : dataql.solvers.registry.attribute
        The ``Attribute`` instance that raised the original exception.
    value : ?
        The value used to call the attribute/function defined by ``attribute``.
    call_args : list or None
        The ``*args`` arguments passed to the call.
    call_kwargs : dict or None
        The ``**kwargs`` arguments passed to the call.
    original_exception : Exception
        The original exception that was raised during the call.

    """

    def __init__(self, attribute, value, args, kwargs, original_exception):
        self.attribute = attribute
        self.value = value
        self.call_args = args
        self.call_kwargs = kwargs
        self.original_exception = original_exception
        super().__init__(str(self))

    def __str__(self):
        return 'An error occurred while calling `%s` (%s arguments)' % (
            self.attribute.name,
            'with' if self.call_args or self.call_kwargs else 'without',
        )


class SourceException(SolversException, metaclass=ABCMeta):
    """Base for exceptions raised by a ``Source`` object."""
    pass


class InvalidSource(SourceException):
    """Raised when the source entry is not a class.

    The exception string exposes the erroneous source.

    Attributes
    ----------
    source : ?
        The thing that is not a class and cannot be used as a source.

    """

    def __init__(self, source):
        self.source = source
        super().__init__(str(self))

    def __str__(self):
        return '%s cannot be used as a source, it must be a class' % (
            self.source
        )


class NotSolvable(SourceException):
    """Exception raised when a value is not solvable by a ``Source`` object.

    The exception string only exposes the source class.

    Attributes
    ----------
    source : dataql.solvers.registry.source
        The ``Source`` object used to try to solve a value.
    value : ?
        A value that is not an instance of the source class (or, if the source has
        ``allow_class=True``, the class itself.

    """

    def __init__(self, source, value):
        self.source = source
        self.value = value
        super().__init__(str(self))

    def __str__(self):
        if self.source.allow_class:
            return 'The `%s` source can only solves the class or instances of this class' % (
                class_repr(self.source.source)
            )
        else:
            return 'The `%s` source can only solve instances of this class' % (
                class_repr(self.source.source)
            )


class RegistryException(SolversException, metaclass=ABCMeta):
    """Base for exceptions raised by a ``Registry`` object."""
    pass


class AlreadyRegistered(RegistryException):
    """Exception raised when a source is already registered in the registry.

    The exception string only exposes the source that is already registered.

    Attributes
    ----------
    registry : dataql.solvers.registry.Registry
        The ``Registry`` object that already has the given source.
    source : class
        The class that is already registered in the registry.

    """

    def __init__(self, registry, source):
        self.registry = registry
        self.source = source
        super().__init__(str(self))

    def __str__(self):
        return 'The `%s` source is already in the registry.' % (
            class_repr(self.source)
        )


class SourceNotFound(RegistryException, KeyError):
    """Exception raised when no source was found in a registry for a class.

    The exception string only exposes the source that is not registered.

    Attributes
    ----------
    registry : dataql.solvers.registry.Registry
        The ``Registry`` object that doesn't contain the given source.
    source : class
        The class that is not in the registry.

    """

    def __init__(self, registry, source):
        self.registry = registry
        self.source = source
        super().__init__(str(self))

    def __str__(self):
        return 'The `%s` source is not in the registry.' % (
            class_repr(self.source)
        )


class SolverNotFound(RegistryException):
    """Exception raised when no solver was found to solve a resource or a filter.

    Attributes
    ----------
    registry : dataql.solvers.registry.Registry
        The ``Registry`` object used to solve a resource.
    obj : dataql.resources.Resource or dataql.resources.BaseFilter
        The (subclass of) ``Resource`` or ``BaseFilter`` object for which there is no solvers.

    """

    def __init__(self, registry, obj):
        self.registry = registry
        self.obj = obj
        super().__init__(str(self))

    def __str__(self):
        return 'No solvers found for this kind of object: `%s`' % (
            class_repr(self.obj),
        )


class SolveFailure(RegistryException):
    """Exception raised when no solver was able to solve a (resource/filter, value) couple.

    This exception string exposes the name and class of the solver and the resource or filter.

    Attributes
    ---------
    registry : dataql.solvers.registry.Registry
        The ``Registry`` object that raised this failed to solve.
    obj : dataql.resources.Resource or dataql.resources.BaseFilter
        The (subclass of) ``Resource`` or ``Filter`` object for which there is no solvers.
    value : ?
        The value for which the registry was not able to solve the resource or filter.

    """

    def __init__(self, registry, obj, value):
        self.registry = registry
        self.obj = obj
        self.value = value
        super().__init__(str(self))

    def __str__(self):
        return 'Unable to solve `<%s%s>`.' % (
            self.obj.__class__.__name__,
            '[%s]' % self.obj.name if hasattr(self.obj, 'name') else ''
        )
