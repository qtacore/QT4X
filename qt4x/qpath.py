#-*- coding: utf-8 -*-
'''QPath
'''

from tuia.qpathparser import QPathParser

class QPath(object):
    '''QPath
    '''
    def __init__(self, qpath_string ):
        self._qpath_string = qpath_string
        
    def dumps(self):
        '''serialize
        '''
        return QPathParser().parse(self._qpath_string)
        
