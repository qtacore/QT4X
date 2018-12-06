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
'''Test Stub
'''

from __future__ import print_function, unicode_literals, absolute_import

import re

from qt4x_sut.event import EnumEvent

class StubService(object):
    '''test stub service
    '''
    def __init__(self, app, wndmgr ):
        self._app = app
        self._wndmgr = wndmgr

    def hello(self):
        return "hello"
        
    def get_window_by_name(self, name ):
        '''get window by name
        '''
        wnd = self._wndmgr.get_window_by_name(name)
        if wnd:
            return id(wnd.getroot())
    
    def find_controls_by_name(self, parent_id, name ):
        '''find controls by name
        '''        
        control_ids = []
        root = self._wndmgr.get_control(parent_id)
        for it in root.iter():
            if it.attrib.has_key("name") and it.attrib["name"] == name:
                control_ids.append(id(it))
        return control_ids
    
    def find_controls(self, parent_id, qpath_locator ):
        '''find controls by QPath
        '''
        root = self._wndmgr.get_control(parent_id)
        controls = [root]
        for selector in qpath_locator:
            if not controls: # not found!
                break
            next_controls = []
            for it in controls:
                next_controls += self._find_controls(it, selector)
            controls = next_controls
        return [ id(it) for it in controls]
        
    def _find_controls(self, root, selector ):
        processed_selector = {}
        for k in selector:
            processed_selector[k.lower()] = selector[k]
        selector = processed_selector        
        if 'maxdepth' in selector:
            maxdepth = selector.pop('maxdepth')[1]
        else:
            maxdepth = 1
        if 'instance' in selector:
            instance = selector.pop('instance')[1]
        else:
            instance = None
                    
        matched_controls = []
        for it in self._children_iter(root, maxdepth):            
            for attr in selector:
                op, val = selector[attr]
                
                attr_dict = it.attrib.copy()
                attr_dict['class'] = it.tag
                if not attr_dict.has_key(attr):
                    break
                if op == "=" and val != attr_dict[attr]:
                    break
                if op == "~=" and not re.match(val, attr_dict[attr]):
                    break
            else:
                matched_controls.append(it)
                
        if instance != None:
            matched_controls = [matched_controls[instance]]
        return matched_controls
    
    def _children_iter(self, root, maxdepth):
        '''return child control iterator by max depth
        '''
        i = iter(root)
        while 1:
            elem = i.next()
            yield elem
            if maxdepth-1 > 0:
                for it in self._children_iter(elem, maxdepth-1):
                    yield it
    
    def get_control_children(self, control_id ):
        '''get control direct children
        '''
        control_ids = []
        for it in list(self._wndmgr.get_control(control_id)):
            control_ids.append(id(it))
        return control_ids
    
    def get_control_attr(self, control_id, name ):
        '''get control attribute
        '''
        return self._wndmgr.get_control(control_id).attrib.get(name)
        
    def set_control_attr(self, control_id, name, val ):
        '''set control attribute
        '''
        self._wndmgr.get_control(control_id).attrib[name] = val
    
    def click_control(self, control_id):
        '''click control
        '''
        self._app.post_message((EnumEvent.Click, {"control_id": control_id}))
        
