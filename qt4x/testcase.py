#-*- coding: utf-8 -*-
'''testcase
'''

from testbase.testcase import TestCase
from qt4x.app import App

class QT4xTestCase(TestCase):
    '''testcase base class
    '''
    def clean_test(self):
        App.kill_all()
        
        
        
