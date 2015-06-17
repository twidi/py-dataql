# py-dataql

Python backend for "Data Query Languages" (like GraphQL and others)

## What is it?

`dataql` is for "Data Query Language". It allows to query data in a simple way.

It is heavily inspired by [GraphQL, from Facebook](https://facebook.github.io/react/blog/2015/05/01/graphql-introduction.html)

I didn't want to force people to think "graph", and I chose a language that is different in some
ways. But this library is written with a base, and we provide a generic parser, but other parsers
could easily be written!

## How it works?

For example, the default generic parser included, `DataQLParser`, allows to ask for data
with this example query:

```
User.get('Elon Musk') {
    name,
    birthday.strftime('%x'),
    companies[
        name,
        date:created_year,
    ]
}
```

And to get data like that:

```python
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
```

The main use is for an API, letting the client asking what it really needs, in only one http query,
without having to update the API endpoints.

The only thing to do on the server side is to define, via a registry, what objects and attributes
are allowed.

## Full example

This repository provides a [full, but simple, example](example.py)

## Installing

This library is available on pypi, but still in alpha version.

```
pip install dataql==0.0.1a1
```

## Documentation

No external documentation yet, but the code is heavily documented
using "[Numpydoc](https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt)":

```
--------------------------------------------------------------------------
File                                   blank        comment           code
--------------------------------------------------------------------------
./__init__.py                              9             33              0
./resources.py                           125            236            135
./parsers/__init__.py                      4              4              1
./parsers/base.py                        123            347             90
./parsers/generic.py                     103            308             55
./parsers/mixins.py                      160            468             69
./solvers/base.py                        104            280             52
./solvers/exceptions.py                    0              0              2
./solvers/registry.py                    129            444            111
./utils.py                                13             37              7
--------------------------------------------------------------------------
SUM:                                     770           2157            522
--------------------------------------------------------------------------
```

You may refer to the [example.py](example.py) file for usage.


## TODO

This prototype is working as expected, but there is a lot of things to do:

- create subclasses for exceptions
- write documentation about how to use `dataql` to get data from a query
- write documentation about how to create its own parser
- test on the the Django ORM (it should work)
- create an advanced solver for Django (using `select_related` and `prefetch_related`)
- allow the use of filters that are not attributes of instances, but simple functions
- allow the retrieval of list or dict entries, not only instance attributes
- tell me

## Tests

There is no external tests for now but there are a lot of examples in the classes and method
docstrings that are valid (and passing!) doctests

## Python version

It's 2015. So `dataql` is written with python 3.4 in mind. No plan to port it to python 2. 

## License

The `dataql` library is under the BSD License. See [LICENSE file](LICENSE)

## Contributing

I created the base for a tool that could be really useful. I may have chose the wrong way for some
things, or maybe the whole project. Tell me. Add issues, create pull requests, define new
languages, or simply enhance the parser.... Feel free to contribute!
 
## Internals

This library is split in two main parts: 

### parsers

`dataql.parsers` include everything that is needed to create a parser to parse a query into what
I named "resources" (for example a field, a list, an object, with filter, arguments...)

Each parser (only one for now) returns the same kind of resources. So there is no need to write
a new solver for a new parser
 
### solvers
 
 `dataql.solvers` is the place where, with a base value and a resource, we can have a result
 matching the query.
 
### Etc
 
 More to come, folks!
 
