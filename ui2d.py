import pyglet
from pyglet.gl import *
from ui2ddraw import *

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
        for control in [c for c in self.ui.controls if c.point_inside(x, y)]:
            control.press(buttons, x, y)

    def on_mouse_release(self, x, y, buttons, modifiers):
        for control in [c for c in self.ui.controls if c.point_inside(x, y)]:
            control.release(buttons, x, y)
        
        for control in [c for c in self.ui.controls if c.active]:
            control.deactivate()
            

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        for control in [c for c in self.ui.controls if c.active]:
            control.drag(buttons, x, y, dx, dy)

class Ui(object):
    
    def __init__(self, window):
        self.window = window
        self.controls = []
        self.batch = pyglet.graphics.Batch()
        self.group = uiGroup(window)
        
        ui_handlers = UiEventHandler(window, self)
        window.push_handlers(ui_handlers)

    def addControl(self, object, attr, type=UiControls.BUTTON, **kwargs):
        if type == UiControls.SLIDER:
            self.controls.append( SliderControl( object, attr, 10, 80, 120, 20, self, **kwargs ) )
            
        elif type == UiControls.TOGGLE:
            self.controls.append( ToggleControl( object, attr, 10, 10, 120, 20, self, **kwargs ) )
        
    

class UiControl(object):
    def __init__(self, object, attr, x, y, w, h, ui, type=UiControls.BUTTON, vmin=0, vmax=100):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.type = type
        
        self.active = False
        
        self.object = object

        if hasattr(object, attr):
            self.attr = attr
        else:
            raise ValueError

        self.title = attr.capitalize()
        self.min = vmin
        self.max = vmax

        self.ui = ui
        
        #self.geo = self.buttonBase()
        self.geo = roundbase2(self.x, self.y, self.w, self.h)
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
        
        self.vertices = self.geo['vertices']
        self.colors = self.geo['colors']
        self.flush_draw()
    
    def flush_draw(self, vertices=True, colors=True):
        len_verts = len(self.geo['vertices'])

        if hasattr(self, "vertex_list"):
            len_vlist = self.vertex_list.get_size()

            # resize vertex list if updating to new shape
            if len_verts//2 != len_vlist:
                self.vertex_list.resize( len_verts//2 )
            
            if vertices:
                self.vertex_list.vertices = self.geo['vertices']
            if colors:
                self.vertex_list.colors = self.geo['colors']
        
        else:
            self.vertex_list = self.ui.batch.add(len_verts//2, 
                                             self.geo['mode'],
                                             self.ui.group,
                                             ('v2f/static', self.geo['vertices']),
                                             ('c3f/static', self.geo['colors'])
                                             )
            

    def point_inside(self, x, y):
        if x < self.x:          return False
        if x > self.x+self.w:   return False
        if y < self.y:          return False
        if y > self.y+self.h:   return False
        return True

    def delete(self):
        self.vertex_list.delete()
    
    # override in subclasses
    def press(self, buttons, x, y):
        pass
    def release(self, buttons, x, y):
        pass
    def drag(self, buttons, x, y, dx, dy):
        pass
    
    def getval(self):
        return getattr(self.object, self.attr)

    def setval(self, newval):
        setattr(self.object, self.attr, min(self.max, max(self.min, newval )) )

    def activate(self):
        self.active = True
        self.update_draw()
        
    def deactivate(self):
        self.active = False
        self.update_draw()
    
    def check_attr(self):
        if hasattr(self.object, self.attr):
            return True
        else:
            print('invalid attribute %s on object %s' % (self.attr, self.object))
            return False
        

class ToggleControl(UiControl):
    
    def press(self, buttons, x, y):
        if buttons & pyglet.window.mouse.LEFT:
            self.activate()
            self.toggle()
    
    def release(self, buttons, x, y):
        if buttons & pyglet.window.mouse.LEFT:
            self.deactivate()
    
    def update_draw(self):
        val = getattr(self.object, self.attr)
        
        #checkmark = [self.x-3, self.y + self.h/3.0, \
        #            self.x-3, self.y + 2*self.h/3.0, \
        #            self.x, self.y + 2*self.h/3.0, \
        #            self.x, self.y + self.h/3.0 ]
        
        #self.vertices = self.geo['vertices']
        #self.colors = self.geo['colors']

        self.label.begin_update()
        if (val):
            self.label.text = self.title + ' on'
        else:
            self.label.text = self.title + ' off'
        self.label.end_update()
        
        self.flush_draw()
    
    def toggle(self):
        self.setval( not self.getval() )
        self.update_draw()

class SliderControl(UiControl):
    
    def press(self, buttons, x, y):
        if buttons & pyglet.window.mouse.LEFT or \
           buttons & pyglet.window.mouse.MIDDLE:
            self.activate()
    
    def release(self, buttons, x, y):
        if buttons & pyglet.window.mouse.LEFT:
            self.deactivate()

    
    def drag(self, buttons, x, y, dx, dy):
        if buttons & pyglet.window.mouse.MIDDLE:
            self.setval( self.getval() + dx )
            self.update_draw()
    
    def update_draw(self):
        val = getattr(self.object, self.attr)
        
        #self.vertices = self.geo['vertices']
        #self.colors = self.geo['colors']
        
        #if self.active:
        #    self.colors = [.6,.6,.6]*(len(self.geo['vertices'])//2)
        #else: 
        #    self.colors = [0.3,0.3,0.3]*(len(self.geo['vertices'])//2)
        
        self.label.begin_update()
        self.label.text = self.title + " %.1f" % val
        self.label.end_update()
        
        self.flush_draw()