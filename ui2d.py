import pyglet
from pyglet.gl import *

class uiGroup(pyglet.graphics.Group):
    def __init__(self, window):
        super(uiGroup, self).__init__()
        
        self.window = window
        
    def set_state(self):
        winsize = self.window.get_size()
        
        glMatrixMode(GL_PROJECTION);
        glLoadIdentity();

        gluOrtho2D(0.0, winsize[0], winsize[1], 0.0);

        glMatrixMode(GL_MODELVIEW);
        glLoadIdentity();
        glTranslatef(0.375, 0.375, 0.0);

        glDisable(GL_DEPTH_TEST);

    def unset_state(self):
        pass


class UiControls(object):
    BUTTON = 1
    
    INACTIVE = 0
    ACTIVE = 1

class UiEventHandler(object):
    def __init__(self, window, ui):
        self.window = window
        self.ui = ui

    def on_draw(self):
        self.ui.batch.draw()

    def on_mouse_press(self, x, y, buttons, modifiers):
        winsize = self.window.get_size()
        y = winsize[1] - y
        
        if buttons & pyglet.window.mouse.LEFT:
            for control in self.ui.controls:
                if control.point_inside(x, y):
                    control.activate()

class Ui(object):
    
    def __init__(self, window):
        self.window = window
        self.controls = []
        self.batch = pyglet.graphics.Batch()
        self.group = uiGroup(window)
        
        ui_handlers = UiEventHandler(window, self)
        window.push_handlers(ui_handlers)

    def addControl(self, type=UiControls.BUTTON):
        self.controls.append( ToggleControl( 10, 10, 40, 20, self.batch, self.group ) )
        
    

class UiControl(object):
    def __init__(self, x, y, w, h, batch, group, type=UiControls.BUTTON):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.type = type
        self.state = UiControls.INACTIVE
        
        vertices = [x, y, 0, \
                    x+w, y, 0, \
                    x+w, y+h, 0, \
                    x, y+h, 0 ]
        colors = [1.0,0.0,1.0]*4
        self.vertex_list = batch.add(len(vertices)//3, 
                                             GL_QUADS,
                                             group,
                                             ('v3f/static', vertices),
                                             ('c3f/static', colors))

    def activate(self):
        self.state = UiControls.ACTIVE
        colors = [0.0,1.0,1.0]*4
        self.vertex_list.colors = colors[:]

    def point_inside(self, x, y):
        if x < self.x:
            return False
        if x > self.x+self.w:
            return False
        if y < self.y:
            return False
        if y > self.y+self.h:
            return False
        return True

    def delete(self):
        self.vertex_list.delete()

class ToggleControl(UiControl):
    def activate(self):
        if self.state == UiControls.INACTIVE:
            self.state = UiControls.ACTIVE
            self.vertex_list.colors = [0.0,1.0,1.0]*4
        else:
            self.state = UiControls.INACTIVE
            self.vertex_list.colors = [1.0,0.0,1.0]*4
