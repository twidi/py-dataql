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
