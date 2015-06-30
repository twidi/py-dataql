#!/usr/bin/env python

from datetime import datetime, date

from dataql.parsers import DataQLParser
from dataql.solvers.registry import Registry, EntryPoints


# Declare our classes

class User:
    users = []

    def __init__(self, name, birthday):
        self.name = name
        self.birthday = birthday

        User.users.append(self)

    @classmethod
    def get(cls, name):
        return [u for u in cls.users if u.name == name][0]

    def companies(self):
        return Company.filter_by_creator(self)


class Company:
    posts = []

    def __init__(self, creator, name, created_year):
        self.creator = creator
        self.name = name
        self.created_year = created_year

        Company.posts.append(self)

    @classmethod
    def filter_by_creator(cls, user):
        return [p for p in cls.posts if p.creator == user]


# Create some data
user = User('Elon Musk', date(1971, 6, 28))
Company(user, 'Paypal', 1999)
Company(user, 'Space X', 2002)


# Register authorized fields
registry = Registry()
registry.register(User, ['get', 'name', 'birthday', 'companies'], allow_class=True)
registry.register(Company, ['name', 'created_year'])
registry.register(date, ['strftime'])


# Example query
query = r'''
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
'''

# Get the result
result = registry.solve_resource(
    # Values that can be called at the very first level
    EntryPoints(registry, User=User),
    # The parser is a standalone part
    DataQLParser(query).data
)

# Compare!
assert result == {
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
