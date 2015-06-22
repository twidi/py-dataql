"""``exceptions`` module of ``dataql.parsers``.

It holds all the exception that may be raised by this module.

"""

from dataql.exceptions import DataQLException


class ParserError(DataQLException):
    """Exception raised when the parser failed to parse a query.

    It is raised when a ``parsimonious.exceptions.ParseError`` is raised, to provide
    a more friendly message, keeping the original exception as attribute.

    This exception string only exposes line and column of the error with a abstract
    from the query starting at the position the error occurred.

    Attributes
    ----------
    original_exception : parsimonious.exceptions.ParseError
        The original exception, with everything needed for the display: text, position...

    """

    def __init__(self, original_exception):
        self.original_exception = original_exception

        super().__init__(str(self))

    def __str__(self):
        pos = self.original_exception.pos

        return (
            'Problem with parsing at line %s, column %s. The non-matching portion of '
            'the text begins with: "%s"'
        ) % (
            self.original_exception.line(),
            self.original_exception.column(),
            self.original_exception.text[pos:pos + 20],
        )
