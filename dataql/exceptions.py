"""``exceptions`` module of ``dataql``.

It currently only holds base exception ``DataQLException`` from which all exceptions that
may be defined in sub modules inherit from..

"""

class DataQLException(Exception):
    """Base for exceptions raised by dataql code."""
    pass
