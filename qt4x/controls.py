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
'''Control
'''

import re
import time

from testbase.util import Timeout, LazyInit
from testbase.platform.jsonrpc import ServerError
from tuia.exceptions import ControlNotFoundError, ControlAmbiguousError, ControlExpiredError
from qt4x.qpath import QPath

CONTROL_EXPIRED_ERROR = 1

def check_expired( func ):
    def _func(*argv, **kwargs):
        try:
            return func(*argv, **kwargs)
        except ServerError, e:
            if e.code == CONTROL_EXPIRED_ERROR:
                raise ControlExpiredError()
            else:
                raise
    return _func
            
class ControlProxy(object):
    '''control proxy
    '''
    def __init__(self, driver, control_id ):
        self._driver = driver
        self._control_id = control_id
    
    @property    
    def id(self):
        return self._control_id
    
    @check_expired
    def get_attr(self, name ):
        return self._driver.get_control_attr(self._control_id, name)

    @check_expired
    def set_attr(self, name, value ):
        return self._driver.set_control_attr(self._control_id, name, value)
        
    @check_expired
    def get_children(self):
        return self._driver.get_control_children(self._control_id)
        
    @check_expired
    def click(self):
        return self._driver.click_control(self._control_id)
        
class Window(object):
    '''Window
    '''
    timeout = 4
    interval = 0.5
    
    NAME = None
    
    def __init__(self, app ):
        self._app = app
        self._driver = app.get_driver()
        self._locators = {}
        self._proxy = LazyInit(self, "_proxy", self._init_proxy)
        
    def _init_proxy(self):
        t0 = time.time()
        while time.time() - t0 < self.timeout:
            if self.NAME is None:
                raise ValueError("NAME of class \"%s\" is not set" % type(self))
            control_id = self._driver.get_window_by_name(self.NAME)
            if control_id:
                return ControlProxy(self._driver, control_id)
            time.sleep(self.interval)
        raise ControlNotFoundError("window with name \"%s\" not found" % self.NAME)
        
    def __getitem__(self, key):
        if not self._locators.has_key(key):
            raise RuntimeError("child control of name \"%s\" is not defined" % key )
        params = self._locators.get(key)

        if isinstance(params, basestring):
            params = {
                "root": self,
                "type": Control,
                "locator": params
            }
        else:
            params["root"] = params.get("root", self)
            params["type"] = params.get("type", Control)
            
        root = params["root"]
        if isinstance(root, basestring) and re.match('^@', root):
            root_key = re.sub('^@', '', root)
            params["root"] = self.controls[root_key]       
        ctrl_class = params.pop("type")
        return ctrl_class(**params)
        
    @property
    def id(self):
        '''control id
        '''
        return self._proxy.id
    
    @property
    def app(self):
        '''belonging app
        '''
        return self._app
    
    @property
    def title(self):
        '''window title
        '''
        return self._proxy.get_attr("title")

    @property
    def controls(self):
        '''children control retriever
        '''
        return self
    
    def get_driver(self):
        '''get test driver
        '''
        return self._driver
        
    def update_locator(self, locators):
        '''update UI locator(UI map)
        '''
        self._locators.update(locators)
        
    def exist(self):
        '''window existence
        '''
        if self.NAME is None:
            raise ValueError("NAME of class \"%s\" is not set" % type(self))
        control_id = self._driver.get_window_by_name(self.NAME)
        if control_id:
            return True
        else:
            return False
    
    def wait_for_exist(self, timeout, interval ):
        '''wait for control existence
        '''
        Timeout(timeout, interval).retry(self.exist, (), None, lambda x:x==True)
    
    def wait_for_value(self, timeout, interval, attrname, attrval ):
        '''wait for control attribute value
        '''
        Timeout(timeout, interval).retry(lambda: getattr(self, attrname),
                                         (), 
                                         None, 
                                         lambda x:x==attrval)
        
class Control(object):
    '''Control
    '''
    def __init__(self, root, locator ):
        '''constructor
        
        :param root: parent control or window
        :param locator: control locator
        '''
        self._root = root
        self._locator = locator
        self._driver = root.get_driver()
        self._proxy = LazyInit(self, "_proxy", self._init_proxy)
    
    def _init_proxy(self):
        if isinstance(self._locator, basestring):
            control_ids = self._driver.find_controls_by_name(self._root.id, self._locator)
        elif isinstance(self._locator, int):
            control_ids = [self._locator]
        elif isinstance(self._locator, QPath):                
            control_ids = self._driver.find_controls(self._root.id, self._locator.dumps()[0])
        else:
            raise TypeError()
        if control_ids:
            if len(control_ids) == 1:
                return ControlProxy(self._driver, control_ids[0])
            else:
                raise ControlAmbiguousError()
        else:
            raise ControlNotFoundError()
        
    @property
    def id(self):
        '''control id
        '''
        return self._proxy.id
    
    @property
    def name(self):
        return self._proxy.get_attr("name")
        
    def get_driver(self):
        '''get test driver
        '''
        return self._driver
    
    def exist(self):
        '''control existence
        '''
        if not self._root.exist():
            return False
        if isinstance(self._locator, basestring):
            control_ids = self._driver.find_controls_by_name(self._root.id, self._locator)
        elif isinstance(self._locator, QPath):
            control_ids = self._driver.find_controls(self._root.id, self._locator.dumps())
        else:
            raise TypeError()
        if control_ids:
            return True
        else:
            return False

    def wait_for_exist(self, timeout, interval ):
        '''wait for control existence
        '''
        Timeout(timeout, interval).retry(self.exist, (), None, lambda x:x==True)
    
    def wait_for_value(self, timeout, interval, attrname, attrval ):
        '''wait for control attribute value
        '''
        Timeout(timeout, interval).retry(lambda: getattr(self, attrname),
                                         (), 
                                         None, 
                                         lambda x:x==attrval)
        
    

class StaticText(Control):
    '''Text edit control
    '''
    
    @property
    def text(self):
        return self._proxy.get_attr("text")
    

class TextEdit(Control):
    '''Text edit control
    '''
    @property
    def text(self):
        return self._proxy.get_attr("text")
    
    @text.setter
    def text(self, content ):
        return self._proxy.set_attr("text", content)
    
    
class MenuItem(Control):
    '''menu item control
    '''
    @property
    def value(self):
        return self._proxy.get_attr("value")

class Menu(Control):
    '''menu control
    '''
    def __iter__(self):
        for control_id in self._proxy.get_children():
            yield MenuItem(self, control_id)
        
    def __len__(self):
        return len(self._proxy.get_children())
    
    
class Button(Control):
    '''button control
    '''
    def click(self):
        self._proxy.click()
        
        
        
