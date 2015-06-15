"""``dataql`` is for "Data Query Language". It allows to query data in a simple way.

For example, the default generic parser included, ``DataQLParser``, allows to ask for data
with this query:

.. code:: python

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

The main use is for an API, letting the client asking what it really needs, in only one http query,
without having to update the API endpoints.

The only thing to do on the server side is to defined, via a registry, what objects and attributes
are allowed.

"""
