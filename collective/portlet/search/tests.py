# -*- coding: utf-8 -*-
import unittest
import doctest

from zope.testing import doctestunit
from zope.component import testing
from Testing import ZopeTestCase as ztc

from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite
from Products.PloneTestCase.layer import onsetup

import collective.portlet.search
def hacked_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

@onsetup
def setup_product():
    fiveconfigure.debug_mode = True
    zcml.load_config('configure.zcml',
                     collective.portlet.search)
    fiveconfigure.debug_mode = False
    ztc.installPackage('collective.portlet.search')
    #Loads all dependencies modules
    for item in PRODUCTS:
        module_name = item[0]
        module = hacked_import(module_name)
        try:
            zcml.load_config('configure.zcml', module)
        except IOError:
            # Produto sem configure.zcml
            continue
    fiveconfigure.debug_mode = False
    for item in PRODUCTS:
        module_name = item[0]
        if module_name.startswith('Products'):
            module_name = module_name[9:]
            ztc.installProduct(module_name)
        else:
            ztc.installPackage(module_name)

setup_product()

ptc.setupPloneSite(products=['collective.portlet.search'],
                   extension_profiles=['collective.portlet.search:default'])

class TestCase(ptc.PloneTestCase):
    class layer(PloneSite):

        @classmethod
        def tearDown(cls):
            pass



def test_suite():
    return unittest.TestSuite([

        # Unit tests
        #doctestunit.DocFileSuite(
        #    'README.txt', package='collective.portlet.search',
        #    setUp=testing.setUp, tearDown=testing.tearDown),

        #doctestunit.DocTestSuite(
        #    module='collective.portlet.search.mymodule',
        #    setUp=testing.setUp, tearDown=testing.tearDown),


        # Integration tests that use PloneTestCase
        ztc.ZopeDocFileSuite(
            'README.txt', package='collective.portlet.search.docs',
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE |
                         doctest.NORMALIZE_WHITESPACE |
                         doctest.ELLIPSIS,
            test_class=TestCase),

        ztc.FunctionalDocFileSuite(
            'browser.txt',
            package='collective.portlet.search.docs',
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE |
                        doctest.NORMALIZE_WHITESPACE |
                        doctest.ELLIPSIS,
            test_class=TestCase),

        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

