#!/usr/bin/env python
"""
(First inspired by https://gist.github.com/ishikawa/559312)

The **run_tests.py** script supports simple test discovery (both `doctest`_ and `unittest`_)
and running discovered tests.

Run `./run_tests.py to see usage.

.. _doctest:  http://docs.python.org/library/doctest.html
.. _unittest: http://docs.python.org/library/unittest.html

"""
 
import argparse
from importlib import import_module
import os

import unittest
import doctest
 

package_name = 'dataql'
top_dir = os.path.abspath(os.path.dirname(__file__))
package_dir = os.path.join(top_dir, package_name)


def get_modules(paths):
    files = [p for p in paths if p.endswith('.py')]

    for dir in [p for p in paths if not p.endswith('.py')]:
        for root_dir, _, sub_files in os.walk(dir):
            files.extend([
                os.path.join(root_dir, f) for f in sub_files if f.endswith('.py')
            ])

    modules = []
    for f in sorted(files):
        module_path = os.path.relpath(f, top_dir).replace('/', '.')[:-3].replace('.__init__', '')
        modules.append(import_module(module_path))

    return modules


def discover(paths):

    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()

    modules = get_modules(paths)

    # doctest
    for module in modules:
        try:
            tests = doctest.DocTestSuite(module)
        except ValueError:
            pass
        else:
            suite.addTest(tests)

    # unittest
    for module in modules:
        name = module.__name__.split(".")[-1]
        if not name.startswith("test_"):
            continue

        tests = loader.loadTestsFromModule(module)
        suite.addTest(tests)

    return suite


def project_path(path):
    if not path.startswith('/'):
        path = os.path.join(top_dir, path)
    path = os.path.normpath(path)

    if package_dir not in path:
        raise argparse.ArgumentTypeError('Path should be "%s" or subdirectory '
                                         'or python file in this tree' % package_dir)

    if not os.path.exists(path):
        raise argparse.ArgumentTypeError('Path "%s" does not exist' % package_dir)

    if path.endswith('.py') and not os.path.isfile(path):
        raise argparse.ArgumentTypeError('Path ending with .py must be a file')

    if not path.endswith('.py') and not os.path.isdir(path):
        raise argparse.ArgumentTypeError('Path must be a directory')

    return path


def main():
    parser = argparse.ArgumentParser(description='Discover and run tests.')
    parser.add_argument('paths', metavar='PATH', type=project_path, nargs='*',
                        default=[package_dir],
                        help='One or more paths (directory or python file) for which tests '
                             'should be run. Default to "dataql", to tests the whole package')

    args = parser.parse_args()

    runner = unittest.TextTestRunner()
    runner.run(discover(paths=args.paths))


if __name__ == "__main__":
    main()
