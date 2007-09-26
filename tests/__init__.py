import doctest
import os
import re
from unittest import defaultTestLoader, TestSuite

test_file_re = re.compile('test\.py$', re.IGNORECASE)
doctests = ['validators']

def suite():
    """
    Creates a ``TestSuite`` containing ``TestCase``s from all modules
    whose filenames end with 'test.py' in this directory and
    ``TestCase``s created from modules which have doctests.
    """
    path = os.path.abspath(os.path.dirname(__file__))
    app_name = os.path.basename(os.path.dirname(path))
    test_files = [f for f in os.listdir(path) if test_file_re.search(f)]
    module_names = ['%s.tests.%s' % (app_name, os.path.splitext(f)[0]) \
                    for f in test_files]
    modules = [__import__(module_name, globals(), locals(), ['']) \
               for module_name in module_names]
    suite = TestSuite([defaultTestLoader.loadTestsFromModule(module) \
                       for module in modules])

    # Create TestCases from modules which have doctests
    doctest_module_names = ['%s.%s' % (app_name, m) for m in doctests]
    doctest_modules = [__import__(module_name, globals(), locals(), ['']) \
                       for module_name in doctest_module_names]
    for doctest_module in doctest_modules:
        suite.addTest(doctest.DocTestSuite(doctest_module))

    return suite
