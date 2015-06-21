#!/usr/bin/env python
"""
(https://gist.github.com/ishikawa/559312)

The **run_tests.py** script supports simple test discovery (both `doctest`_ and `unittest`_)
and running discovered tests.

 * ``-s DIRECTORY``  Directory to start discovery ('.' default)
 * ``-t DIRECTORY``  Top level directory of project (default to start directory)

How to use::

    % PYTHONPATH=.:project_dir python tests/runtests.py -s . -t project_dir

.. _doctest:  http://docs.python.org/library/doctest.html
.. _unittest: http://docs.python.org/library/unittest.html

"""
 
import sys
import os
from os.path import exists, join
 
import unittest
import doctest
 
 
def walk_modules(root_dir):
    """Generate the modules in a directory tree by walking the tree."""
 
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs
                           if not d.startswith(".") and
                              exists(join(root, d, "__init__.py"))]
        files[:] = ["" if f.startswith("__init__") else f[:-3]
                            for f in files
                                  if f.endswith(".py")]
 
        root = relpath(root, root_dir)
 
        if not root or root == ".":
            continue
 
        root = root.split("/")
        modules = [root + [f] if f else root for f in files]
 
        for name in [".".join(m) for m in modules]:
            __import__(name)
            yield sys.modules[name]
 
def relpath(path, start):
    if hasattr(os.path, "relpath"):
        return os.path.relpath(path, start)
    else:
        # os.path.relpath is new in 2.6
        import re
        from os.path import normpath
 
        pattern = normpath(start)
        pattern = re.compile(r'^%s/?' % re.escape(pattern))
        return pattern.sub('', normpath(path))
 
def discover(start_directory, top_directory=None):
 
    if not top_directory:
        top_directory = start_directory
 
    loader = unittest.defaultTestLoader
    suite  = unittest.TestSuite()
 
    # doctest
    for module in walk_modules(top_directory):
        try:
            tests = doctest.DocTestSuite(module)
        except ValueError as e:
            pass
        else:
            suite.addTest(tests)
 
    # unittest
    for module in walk_modules(start_directory):
        name = module.__name__.split(".")[-1]
        if not name.startswith("test_"):
            continue
 
        tests = loader.loadTestsFromModule(module)
        suite.addTest(tests)
 
    return suite
 
def main():
    from optparse import OptionParser
 
    parser = OptionParser()
    parser.add_option("-s", "--start",
                      dest="start", default=".",
                      help="Directory DIRECTORY to start discovery ('.' default)",
                      metavar="DIRECTORY")
    parser.add_option("-t", "--top",
                      dest="top",
                      help="Top level directory of project (default to start directory)",
                      metavar="DIRECTORY")
 
    (options, args) = parser.parse_args()
 
    runner = unittest.TextTestRunner()
    runner.run(discover(
                start_directory=options.start,
                top_directory=options.top))
 
 
if __name__ == "__main__":
    main()

