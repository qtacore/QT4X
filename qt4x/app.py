#-*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QTA available.
# Copyright (C) 2016THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the BSD 3-Clause License (the "License"); you may not use this 
# file except in compliance with the License. You may obtain a copy of the License at
# 
# https://opensource.org/licenses/BSD-3-Clause
# 
# Unless required by applicable law or agreed to in writing, software distributed 
# under the License is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
#
'''Application
'''

import subprocess
from testbase.platform.jsonrpc import ServerProxy

class App(object):
    '''Application
    '''
    
    ENTRY = None
    PORT = None
    
    _instances = []
    
    def __init__(self):
        self._driver = None
        self._p = subprocess.Popen(["python", "-m", self.ENTRY, str(self.PORT)])
        self._instances.append(self)
        
    @property
    def pid(self):
        return self._p.pid
    
    def get_driver(self):
        if self._driver is None:
            self._driver = ServerProxy("http://127.0.0.1:%s" % self.PORT)
        return self._driver
    
    def stop(self):
        self._p.terminate()
        
    def kill(self):
        self._p.kill()
    
    @classmethod
    def kill_all(cls):
        for it in cls._instances:
            it.kill()
        
if __name__ == '__main__':
    app = App()
    print app.pid
    app.stop()
