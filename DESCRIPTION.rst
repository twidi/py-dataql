py-dataql
=========

Python backend for "Data Query Languages" (like GraphQL and others

What is it?
-----------

``dataql`` is for "Data Query Language". It allows to query data in a
simple way.

It is heavily inspired by `GraphQL, from
Facebook <https://facebook.github.io/react/blog/2015/05/01/graphql-introduction.html>`__

I didn't want to force people to think "graph", and I chose a language
that is different in some ways. But this library is written with a base,
and we provide a generic parser, but other parsers could easily be
written!

How it works?
-------------

For example, the default generic parser included, ``DataQLParser``,
allows to ask for data with this example query:

::

    User.get('Elon Musk') {
        name,
        birthday.strftime('%x'),
        companies[
            name,
            date:created_year,
        ]
    }

And to get data like that:

.. code:: python

    {
        'name': 'Elon Musk',
        'birthday': '06/28/71',
        'companies': [
            {
                'name': 'Paypal',
                'date': 1999
            },
            {
                'name': 'Space X',
                'date': 2002
            }
        ]
    }

The main use is for an API, letting the client asking what it really
needs, in only one http query, without having to update the API
endpoints.

The only thing to do on the server side is to define, via a registry,
what objects and attributes are allowed.
