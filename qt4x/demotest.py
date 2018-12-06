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
'''Test for demo App
'''

from qt4x.testcase import QT4xTestCase
from qt4x.app import App
from qt4x.qpath import QPath
from qt4x.controls import Window, Button, StaticText

class TextEditorApp(App):
    """Text editor app
    """
    ENTRY = "qt4x_sut.demo"
    PORT = "11200"

class MainWindow(Window):
    """main window
    """
    NAME = "Main"
    
    def __init__(self, app):
        super(MainWindow, self).__init__(app)
        self.update_locator({
            "About Button": {"type": Button, "locator": "about_btn"}
        })
        
    def open_about_window(self):
        '''open about window
        '''
        self.controls["About Button"].click()
        about = AboutWindow(self.app)
        about.wait_for_exist(5,1)
        return about
        
class AboutWindow(Window):
    """about window
    """
    NAME = "About"
    
    def __init__(self, app):
        super(AboutWindow, self).__init__(app)
        self.update_locator({
            "Content": {"type": StaticText, "locator":QPath("/class='StaticText'") }
        })
        
class HelloTest(QT4xTestCase):
    """Test for demo App
    """
    owner = "foo"
    timeout = 2
    priority = QT4xTestCase.EnumPriority.High
    status = QT4xTestCase.EnumStatus.Ready
    
    def run_test(self):
        
        #-----------------------
        self.start_step("start app")
        #-----------------------
        app = TextEditorApp()
        
        #-----------------------
        self.start_step("show about")
        #-----------------------
        mainwnd = MainWindow(app)
        aboutwnd = mainwnd.open_about_window()
        self.assert_equal("check about content", 
                          aboutwnd.controls["Content"].text, 
                          "Text editor V 1.0.0")
        
if __name__ == '__main__':
    HelloTest().debug_run()
        
        
        
        
        
    
