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
'''UI Framework

Fake UI framework, using `etree` as UI element tree.
'''

from __future__ import print_function, unicode_literals, absolute_import

import collections
import threading
import StringIO
from xml.etree import ElementTree

from qt4x.jsonrpc import SimpleJSONRPCServer
from qt4x_sut.stub import StubService
from qt4x_sut.event import EnumEvent

class MsgQueue(object):
    '''Message queue
    '''
    def __init__(self):
        self._queue = collections.deque()
        self._not_empty_cond = threading.Condition()
        
    @property
    def empty(self):
        '''is queue empty
        '''
        return not self._queue
    
    def get(self):
        '''get message
        '''
        with self._not_empty_cond:
            if self.empty:
                self._not_empty_cond.wait()
            msg = self._queue.popleft()
            return msg
        
    def put(self, msg):
        '''put message
        '''
        with self._not_empty_cond:
            if msg not in self._queue:
                self._queue.append(msg)
                self._not_empty_cond.notify()

class WindowManager(object):
    '''Window manager
    '''
    def __init__(self):
        self._windows = {}
        self._curr_window = None
        
    def register_window(self, name, layout):
        '''register a window
        '''
        self._windows[name] = ElementTree.parse(StringIO.StringIO(layout)) 
        
    def render_window(self, name ):
        '''render a window
        '''
        self._curr_window = name
        
    def get_current_window(self):
        '''get current top window
        '''
        return self._windows[self._curr_window]
    
    def get_window_by_name(self, name ):
        '''get window by name
        '''
        return self._windows.get(name)
        
    def get_control(self, control_id ):
        '''get control by ID
        '''
        for wnd in self._windows.values():
            for it in wnd.iter():
                if id(it) == control_id:
                    return it
        
class App(object):
    '''Application
    '''
    def __init__(self, port ):
        self._port = port
        self._wndmgr = WindowManager()
        self._msgqueue = MsgQueue()
        
        #test stub thread
        self._rpc_server = threading.Thread(target=self._rpc_server_thread)
        self._rpc_server.setDaemon(1)
        self._rpc_server.start()
        
    def _rpc_server_thread(self):
        '''test stub service thread
        '''
        rpc_server = SimpleJSONRPCServer(("", self._port), logRequests=False)
        rpc_server.register_instance(StubService(self, self._wndmgr))
        rpc_server.serve_forever()
        
    def register_window(self, name, layout ):
        '''register a window
        '''
        self._wndmgr.register_window(name, layout)
        
    def render_window(self, name ):
        '''render a window
        '''
        self._msgqueue.put((EnumEvent.RenderWindow, {"name":name}))
                
    def run_loop(self):
        '''app event loop
        '''
        self.on_created()
        while 1:
            event, params = self._msgqueue.get()
            if event == EnumEvent.Stop:
                break
            elif event == EnumEvent.RenderWindow:
                self._wndmgr.render_window(params["name"])
            elif event == EnumEvent.Click:
                control = self._wndmgr.get_control(params["control_id"])
                self.on_click(control)
        self.on_destroyed()
        
    def on_created(self):
        '''create callback
        '''
        pass

    def on_destroying(self):
        '''destroy callback
        '''
        pass
    
    def on_click(self, control ):
        '''click event callback
        '''
        pass
    
    def post_message(self, msg ):
        '''post message to app
        '''
        self._msgqueue.put(msg)


