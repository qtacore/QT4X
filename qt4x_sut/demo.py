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
'''Demo App
'''

from __future__ import print_function, unicode_literals, absolute_import

import os
import sys

from qt4x_sut.app import App

MAIN_LAYOUT = """
<Window>
    <TitleBar name="title" text="Text editor"/>
    <MenuBar name="menu" >
        <Menu text="File" >
            <MenuItem value="Open file" />
            <MenuItem value="Save file" />
        </Menu>
        <Menu text="Help">
            <MenuItem value="Help" />
            <MenuItem value="About">
                <Buttom name="about_btn"/>
            </MenuItem>
        </Menu>
    </MenuBar>
    <TextEdit name="editor" text="input here..." />
</Window>
"""

ABOUT_LAYOUT = """
<Window>
    <TitleBar name="title" text="About"/>
    <StaticText text="Text editor V 1.0.0" />
</Window>
"""

class TextEditorApp(App):
    '''text editor app
    '''
    def on_created(self):
        self.register_window("Main", MAIN_LAYOUT)
        self.register_window("About", ABOUT_LAYOUT)
        self.render_window("Main")
        
    def on_click(self, control ):
        if control.attrib["name"] == "about_btn":
            self.render_window("About")
        
def app_main():
    if len(sys.argv) <= 1:
        sys.stderr.write("Usage:\n\t%s LISTEN_PORT" % os.path.basename(sys.argv[0]))
        sys.exit(1)
    port = int(sys.argv[1])
    app = TextEditorApp(port)
    app.run_loop()
    
if __name__ == '__main__':
    app_main()
    #app = TextEditorApp(111)
    #app.run_loop()
        
