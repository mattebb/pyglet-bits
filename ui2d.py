import pyglet
from pyglet.gl import *

class uiGroup(pyglet.graphics.Group):
    def __init__(self, window):
        super(uiGroup, self).__init__()
        
        self.window = window
        
    def set_state(self):
        winsize = self.window.get_size()
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        glOrtho(0.0, winsize[0], 0.0, winsize[1], -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.375, 0.375, 0.0)

        glDisable(GL_DEPTH_TEST);

    def unset_state(self):
        pass



class UiControls(object):
    BUTTON = 1
    TOGGLE = 2
    SLIDER = 3
    
    INACTIVE = 0
    ACTIVE = 1

class UiEventHandler(object):
    def __init__(self, window, ui):
        self.window = window
        self.ui = ui

    def on_draw(self):
        self.ui.batch.draw()

    def on_mouse_press(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            for control in [c for c in self.ui.controls if c.point_inside(x, y)]:
                control.press(x, y)

    def on_mouse_release(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:

            for control in [c for c in self.ui.controls if c.point_inside(x, y)]:
                control.release(x, y)
            
            for control in [c for c in self.ui.controls if c.active]:
                control.deactivate()
            

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            for control in [c for c in self.ui.controls if c.active]:
                control.drag(x, y, dx, dy)
                
            #for control in [c for c in self.ui.controls if c.point_inside(x, y)]:
            #    control.drag(x, y, dx, dy)

class Ui(object):
    
    def __init__(self, window):
        self.window = window
        self.controls = []
        self.batch = pyglet.graphics.Batch()
        self.group = uiGroup(window)
        
        ui_handlers = UiEventHandler(window, self)
        window.push_handlers(ui_handlers)

    def addControl(self, object, attr, type=UiControls.BUTTON):
        if type == UiControls.SLIDER:
            self.controls.append( SliderControl( object, attr, 10, 40, 80, 20, self ) )
            
        elif type == UiControls.TOGGLE:
            self.controls.append( ToggleControl( object, attr, 10, 10, 80, 20, self ) )
        
    

class UiControl(object):
    def __init__(self, object, attr, x, y, w, h, ui, type=UiControls.BUTTON):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.type = type
        
        self.active = False
        
        self.object = object
        self.attr = attr
        
        self.ui = ui
        
        self.title = attr.capitalize()
        
        self.label = pyglet.text.Label(self.title,
                        batch=ui.batch,
                        group=ui.group,
                        font_size=10,
                        color = [0,0,0,255],
                        x=x+2, y=y+2)
        
        self.update_draw()

    def buttonBase(self):
        return [self.x, self.y, \
                self.x+self.w, self.y, \
                self.x+self.w, self.y+self.h, \
                self.x, self.y+self.h ]

    def update_draw(self):
        
        self.vertices = self.buttonBase()
        self.colors = [1.0,0.0,1.0]*(len(self.vertices)//2)
        
        self.flush_draw()
    
    def flush_draw(self, vertices=True, colors=True):
        if hasattr(self, "vertex_list"):
            
            # resize vertex list if updating to new shape
            if len(self.vertices)//2 != self.vertex_list.get_size():
                self.vertex_list.resize( len(self.vertices)//2 )
            
            if vertices:
                self.vertex_list.vertices = self.vertices
            if colors:
                self.vertex_list.colors = self.colors
        
        else:
            self.vertex_list = self.ui.batch.add(len(self.vertices)//2, 
                                             GL_QUADS,
                                             self.ui.group,
                                             ('v2f/static', self.vertices),
                                             ('c3f/static', self.colors))
            

    def point_inside(self, x, y):
        if x < self.x:          return False
        if x > self.x+self.w:   return False
        if y < self.y:          return False
        if y > self.y+self.h:   return False
        return True

    def delete(self):
        self.vertex_list.delete()
    
    # override in subclasses
    def press(self, x, y):
        pass
    def release(self, x, y):
        pass
    def drag(self, x, y, dx, dy):
        pass
    
    def activate(self):
        self.active = True
        
    def deactivate(self):
        self.active = False
    
    def check_attr(self):
        if hasattr(self.object, self.attr):
            return True
        else:
            print('invalid attribute %s on object %s' % (self.attr, self.object))
            return False
        

class ToggleControl(UiControl):
    
    def press(self, x, y):
        self.activate()
        self.toggle()
    
    def release(self, x, y):
        self.deactivate()
    
    def update_draw(self):
        val = getattr(self.object, self.attr)
        
        checkmark = [self.x-3, self.y + self.h/3.0, \
                    self.x-3, self.y + 2*self.h/3.0, \
                    self.x, self.y + 2*self.h/3.0, \
                    self.x, self.y + self.h/3.0 ]
        
        self.label.begin_update()
        
        if (val):
            self.vertices = self.buttonBase() + checkmark
            self.colors = [1.0,0.0,1.0]*(len(self.vertices)//2)
            self.label.text = self.title + ' on'
        else:
            self.vertices = self.buttonBase()
            self.colors = [0.5,0.0,0.5]*(len(self.vertices)//2)
            self.label.text = self.title + ' off'
        
        self.label.end_update()
        
        self.flush_draw()
    
    def toggle(self):
        if not self.check_attr(): return
        
        val = getattr(self.object, self.attr)
        setattr(self.object, self.attr, not val)
        
        self.update_draw()

class SliderControl(UiControl):
    
    def press(self, x, y):
        self.activate()
    
    def release(self, x, y):
        self.deactivate()
    
    def drag(self, x, y, dx, dy):
        if not self.check_attr(): return

        val = getattr(self.object, self.attr)
        setattr(self.object, self.attr, val + dx)
        