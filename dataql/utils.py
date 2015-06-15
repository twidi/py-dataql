"""``utils`` module of ``dataql``.

Provide some simple utilities.

"""

def class_repr(value):
    """Returns a representation of the value class.

    Arguments
    ---------
    value
        A class or a class instance

    Returns
    -------
    str
        The "module.name" representation of the value class.

    Example
    -------
    >>> from datetime import date
    >>> class_repr(date)
    'datetime.date'
    >>> class_repr(date.today())
    'datetime.date'
    """
    klass = value
    if not isinstance(value, type):
        klass = klass.__class__
    return '.'.join([klass.__module__, klass.__name__])


def isclass(value):
    """Tell if the value is a class or not.

    Arguments
    ---------
    value
        Value to test if its a class or not.

    Returns
    -------
    boolean
        ``True`` if the value is a class, ``False`` otherwise.

    Example
    -------

    >>> from datetime import date
    >>> isclass(date)
    True
    >>> isclass(date.today())
    False

    """
    return isinstance(value, type)
