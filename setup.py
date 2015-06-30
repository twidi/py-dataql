#!/usr/bin/env python

import ast

import codecs
import os

from pip.req import parse_requirements
from setuptools import setup, find_packages


# Configuration
package_name = 'dataql'
long_doc_file = 'DESCRIPTION.rst'

classifiers = [
    "Development Status :: 4 - Beta",
    "Operating System :: OS Independent",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.4",
    "Topic :: Software Development :: Libraries",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

# Code
# The `session` argument for the `parse_requirements` function is available (but
# optional) in pip 1.5, and mandatory in next versions
try:
    from pip.download import PipSession
except ImportError:
    parse_args = {}
else:
    parse_args = {'session': PipSession()}


def get_requirements(source):
    install_reqs = parse_requirements(source, **parse_args)
    return set([str(ir.req) for ir in install_reqs])


class VersionFinder(ast.NodeVisitor):
    def __init__(self):
        self.data = {}

    def visit_Assign(self, node):
        if node.targets[0].id in (
                '__version__',
                '__author__',
                '__contact__',
                '__homepage__',
                '__license__',
        ):
            self.data[node.targets[0].id[2:-2]] = node.value.s


def read(*path_parts):
    filename = os.path.join(os.path.dirname(__file__), *path_parts)
    with codecs.open(filename, encoding='utf-8') as fp:
        return fp.read()


def find_info(*path_parts):
    finder = VersionFinder()
    node = ast.parse(read(*path_parts))
    finder.visit(node)
    info = finder.data
    info['docstring'] = ast.get_docstring(node)
    return info


package_info = find_info(package_name, '__init__.py')

setup(
    name=package_name,
    version=package_info['version'],
    packages=find_packages(),
    include_package_data=True,
    description=package_info['docstring'],
    long_description=read(long_doc_file),
    url=package_info['homepage'],
    author=package_info['author'],
    author_email=package_info['contact'],
    install_requires=get_requirements('requirements.txt'),
    license=package_info['license'],
    classifiers=classifiers,
)
