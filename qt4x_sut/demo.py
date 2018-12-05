#-*- coding: utf-8 -*-
'''Demo App
'''

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
        
