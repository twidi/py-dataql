"""``exceptions`` module of ``dataql``.

It currently only holds base exception ``DataQLException`` from which all exceptions that
may be defined in sub modules inherit from..

"""

from abc import ABCMeta


class DataQLException(Exception, metaclass=ABCMeta):
    """Base for exceptions raised by dataql code."""
    pass
