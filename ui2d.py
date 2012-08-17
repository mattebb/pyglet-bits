import pyglet
from pyglet.gl import *
from pyglet.window import key
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
            control.press(x, y, buttons, modifiers)
        
        for control in [c for c in self.ui.controls if c.textediting \
                                                and not c.point_inside(x, y)]:
            control.textedit_end()

    def on_mouse_release(self, x, y, buttons, modifiers):
        for control in [c for c in self.ui.controls if c.point_inside(x, y)]:
            control.release(x, y, buttons, modifiers)
        
        #for control in [c for c in self.ui.controls if c.active]:
        #    control.deactivate()
            

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        for control in [c for c in self.ui.controls if c.active]:
            control.drag(x, y, dx, dy, buttons, modifiers)
    
    def on_text(self, text):
        for control in [c for c in self.ui.controls if c.textediting]:
            control.textedit_update(text)
    
    def on_key_press(self, symbol, modifiers):
        if symbol in (key.ENTER, key.RETURN, key.NUM_ENTER, key.ESCAPE):
            for control in [c for c in self.ui.controls if c.textediting]:
                control.textedit_end()
            return pyglet.event.EVENT_HANDLED

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
            self.controls.append( SliderControl( object, attr, 10, 80, 120, 16, self, **kwargs ) )
            
        elif type == UiControls.TOGGLE:
            self.controls.append( ToggleControl( object, attr, 10, 10, 120, 16, self, **kwargs ) )
        

    

class UiControl(object):
    def __init__(self, object, attr, x, y, w, h, ui, type=UiControls.BUTTON, vmin=0, vmax=100):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.type = type
        
        self.active = False
        self.textediting = False
        self.textedit_buffer = ''
        
        self.object = object
        if hasattr(object, attr):
            self.attr = attr
        else:
            raise ValueError("Invalid attribute provided: %s" % attr)

        self.title = attr.capitalize()
        self.min = vmin
        self.max = vmax

        self.ui = ui
        self.geo = roundbase(self.x, self.y, self.w, self.h, [0.5,0.5,0.5], [0.6,0.6,0.6])

        self.label = pyglet.text.Label(self.title,
                        batch=ui.batch,
                        group=ui.group,
                        font_size=9,
                        color = [0,0,0,255],
                        x=x+4, y=y+4)
        
        self.valuelabel = pyglet.text.Label('')
        self.document = pyglet.text.document.UnformattedDocument('testdocument')
        #self.document.set_style(0, len(self.document.text), 
        #    dict(color=(0, 0, 0, 255))
        #)
        #font = self.document.get_font()
        #height = font.ascent - font.descent

        self.layout = pyglet.text.layout.IncrementalTextLayout(
                        self.document, w, h, multiline=False,
                        batch=ui.batch)
        self.caret = pyglet.text.caret.Caret(self.layout)

        self.layout.x = x + 500
        self.layout.y = y + 500
        
        '''
        self.valuelabel = pyglet.text.Label( '' ,
                        batch=ui.batch,
                        group=ui.group,
                        font_size=9,
                        color = [0,0,0,255],
                        x=x+46, y=y+4)
        '''
        self.update_draw()

    def update_draw(self):
        self.vertices = self.geo['vertices']
        self.colors = self.geo['colors']
        self.flush_draw()
    
    def flush_draw(self, vertices=True, colors=True):
        if self.geo != None:
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

    def setval_text(self):
        val = float(self.textedit_buffer)
        setattr(self.object, self.attr, min(self.max, max(self.min, val )) )

    def textedit_begin(self):
        self.textediting = True
        self.caret.visible = True
        self.caret.mark = 0
        self.caret.position = len(self.document.text)
        
        self.update_draw()

    def textedit_update(self, text):
        
        self.caret.on_text(text)
        
        
        #self.textedit_buffer += text
        
        #if self.textediting:
        #    self.setval_text()
        self.update_draw()
        
    def textedit_end(self):
        self.textediting = False
        self.caret.visible = False
        self.caret.mark = self.caret.position = 0
        #self.textedit_buffer = ''
        self.update_draw()

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
    
    def press(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.activate()
            self.toggle()
    
    def release(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.deactivate()
    
    def update_draw(self):
        val = getattr(self.object, self.attr)
        
        if self.active:
            col1 = [0.3,0.3,0.3]
            col2 = [0.4,0.4,0.4]
        else:
            col1 = [0.5,0.5,0.5]
            col2 = [0.6,0.6,0.6]
        
        self.geo = roundbase(self.x, self.y, self.w, self.h, col1, col2)

        self.label.begin_update()
        self.valuelabel.text = "on" if self.getval() else "off"
        self.label.end_update()
        
        
        self.flush_draw()
    
    def toggle(self):
        self.setval( not self.getval() )
        self.update_draw()

class SliderControl(UiControl):
    
    def press(self, x, y, buttons, modifiers):
        if self.textediting:
            self.caret.on_mouse_press(x, y, button, modifiers)
            return pyglet.event.EVENT_HANDLED
        
        if buttons & pyglet.window.mouse.LEFT:
            self.textedit_begin()
            #self.activate()
        elif buttons & pyglet.window.mouse.MIDDLE:
            self.activate()
    
    def release(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.MIDDLE:
            self.deactivate()

    
    def drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & pyglet.window.mouse.MIDDLE:
            self.setval( self.getval() + dx )
            self.update_draw()
    
    def update_draw(self):
        if self.active or self.textediting:
            col1 = [0.3,0.3,0.3]
            col2 = [0.4,0.4,0.4]
        else:
            col1 = [0.5,0.5,0.5]
            col2 = [0.6,0.6,0.6]
        
        self.geo = roundbase(self.x, self.y, self.w, self.h, col1, col2)
        
        print(self.document.text)
        
        #self.valuelabel.begin_update()
        #self.valuelabel.text = " %.1f" % self.getval()
        #self.valuelabel.end_update()
        
        self.flush_draw()