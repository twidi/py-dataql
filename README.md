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
    companies[{
        name,
        year:created_year,
    }],
    company_names: companies[name],
    first_company:companies.0.name,
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
            'year': 1999
        },
        {
            'name': 'Space X',
            'year': 2002
        }
    ],
    'company_names': ['Paypal', 'Space X'],
    'first_company': 'Paypal',
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
pip install dataql==0.1
```

## Documentation

No external documentation yet, but the code is heavily documented
using "[Numpydoc](https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt)":

```
---------------------------------------------------------------------------
File                                   blank        comment           code
---------------------------------------------------------------------------
./__init__.py                              2              1              5
./exceptions.py                            5              5              3
./parsers/__init__.py                      4              4              1
./parsers/base.py                        142            383            120
./parsers/exceptions.py                   13             13             15
./parsers/generic.py                     150            477             86
./parsers/mixins.py                      268            778            110
./resources.py                           144            266            168
./solvers/exceptions.py                   91            112            140
./solvers/filters.py                      63            145             27
./solvers/registry.py                    259            905            213
./solvers/resources.py                   110            316             55
./utils.py                                 6             20              5
---------------------------------------------------------------------------
SUM:                                    1257           3425            948
---------------------------------------------------------------------------
```

You may refer to the [example.py](example.py) file for usage.


## TODO

This prototype is working as expected, but there is a lot of things to do:

- ~~create subclasses for exceptions~~
- ~~allow the use of filters that are not attributes of instances, but simple functions~~
- ~~allow the retrieval of list entries or dict entries, not only instance attributes~~
- ~~allow returning lists of values, not only objects~~
- write documentation about how to use `dataql` to get data from a query
- write documentation about how to create its own parser
- ~~test on the the Django ORM~~ (works)
- create an advanced solver for Django (using `select_related` and `prefetch_related`)
- tell me

## Tests

There are no external tests for now but there are a lot of examples in the classes and method
docstrings that are valid (and passing!) doctests.

You can launch all these doctests this way (at the root of the repository) :

```sh
./run_tests.sh
Ran 109 tests in 0.303s

OK
```

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
 
