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
        #glTranslatef(0.375, 0.375, 0.0)

        glDisable(GL_DEPTH_TEST);

    def unset_state(self):
        pass



class UiControls(object):
    BUTTON = 1
    TOGGLE = 2
    SLIDER = 3
    
    INACTIVE = 0
    ACTIVE = 1
    
    font_style = {'color': (0, 0, 0, 255),
             'font_size': 8,
             'font_name': 'Bitstream Vera Sans', 
             }

class UiEventHandler(object):
    def __init__(self, window, ui):
        self.window = window
        self.ui = ui

    def on_draw(self):
        self.ui.batch.draw()

    def on_mouse_press(self, x, y, buttons, modifiers):
        for control in [c for c in self.ui.controls if c.point_inside(x, y)]:
            control.press(x, y, buttons, modifiers)
        
        #for control in [c for c in self.ui.controls if c.textediting \
        #                                        and not c.point_inside(x, y)]:
        #    control.textedit_end()

    def on_mouse_release(self, x, y, buttons, modifiers):
        for control in [c for c in self.ui.controls if c.point_inside(x, y)]:
            control.release(x, y, buttons, modifiers)
        
        for control in [c for c in self.ui.controls if c.active 
                                                    and not c.point_inside(x, y)]:
            control.release_outside(x, y, buttons, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        for control in [c for c in self.ui.controls if c.point_inside(x, y) or c.active]:
            control.drag(x, y, dx, dy, buttons, modifiers)
    
    def on_text(self, text):
        for control in [c for c in self.ui.controls if c.textediting]:
            control.textedit_update(text)
    
    def on_key_press(self, symbol, modifiers):
        if symbol in (key.ENTER, key.RETURN, key.NUM_ENTER):
            for control in [c for c in self.ui.controls if c.textediting]:
                control.textedit_confirm()
            return pyglet.event.EVENT_HANDLED
        elif symbol == key.ESCAPE:
            for control in [c for c in self.ui.controls if c.textediting]:
                control.textedit_cancel()
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

        self.object = object
        if hasattr(object, attr):
            self.attr = attr
        else:
            raise ValueError("Invalid attribute provided: %s" % attr)

        self.min = vmin
        self.max = vmax

        self.ui = ui
        self.geo = roundbase(self.x, self.y, self.w, self.h, [0.5]*3, [0.6]*3)

        self.title = attr.capitalize()
        self.label = pyglet.text.Label(self.title,
                        batch=ui.batch,
                        group=ui.group,
                        x=x+8, y=y+4,
                        **UiControls.font_style)
        self.label.anchor_y = 'baseline'
        self.label.height = h
        
        self.update_draw()

    def flush_draw(self, vertices=True, colors=True):
        
        #for shape in geo:
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

    def flush_draw2(self):
        for shape in shapes:
            if 'vertex_list' not in shape.keys():
                shape['vertex_list'] = self.ui.batch.add( shape['len'], 
                                             shape['mode'],
                                             self.ui.group,
                                             ('v2f/static', shape['vertices']),
                                             ('c3f/static', shape['colors'])
                                             )
            elif shape['len'] != shape.vertex_list.get_size():
                shape['vertex_list'].vertices = shape.vertices
                shape['vertex_list'].colors = shape.colors

    def point_inside(self, x, y):
        if x < self.x:          return False
        if x > self.x+self.w:   return False
        if y < self.y:          return False
        if y > self.y+self.h:   return False
        return True

    def delete(self):
        self.vertex_list.delete()
    
    # override in subclasses
    def update_draw(self):
        self.flush_draw()
    
    def press(self, *args, **kwargs):
        pass
    def release(self, *args, **kwargs):
        pass
    def drag(self, *args, **kwargs):
        pass
    def release_outside(self, x, y, buttons, modifiers):
        self.deactivate()
    
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
        

class UiTextEditControl(UiControl):
    def __init__(self, object, attr, x, y, w, h, ui, type=UiControls.BUTTON, vmin=0, vmax=100):
        super(UiTextEditControl, self).__init__( object, attr, x, y, w, h, ui, type, vmin, vmax )

        self.document = pyglet.text.document.UnformattedDocument( str(self.getval()) )
        self.document.set_style(0, len(self.document.text), UiControls.font_style)

        self.layout = pyglet.text.layout.IncrementalTextLayout(
                        self.document, w, h, multiline=False,
                        batch=ui.batch,
                        group=ui.group,
                        )
        self.caret = pyglet.text.caret.Caret(self.layout)
        self.caret.visible = False
        
        self.layout.anchor_y = 'baseline'
        self.layout.x = x + 48
        self.layout.y = y + 4
        
        self.text_from_val()
        
        self.update_draw()
    
    def val_from_text(self):
        try:
            val = float(self.document.text)
            setattr(self.object, self.attr, min(self.max, max(self.min, val )) )
        except:
            pass

    def text_from_val(self):
        self.document.text = " %.1f" % self.getval()

    def textedit_begin(self):
        self.activate()

        self.textediting = True
        self.caret.visible = True
        self.caret.mark = 0
        self.caret.position = len(self.document.text)
        self.update_draw()

    def textedit_update(self, text):
        self.caret.on_text(text)
        self.update_draw()
        
    def textedit_end(self):
        self.deactivate()
        self.textediting = False
        self.caret.visible = False
        self.caret.mark = self.caret.position = 0
        self.update_draw()
    
    def textedit_confirm(self):
        if not self.textediting: return
        self.val_from_text()
        self.text_from_val()
        self.textedit_end()
    
    def textedit_cancel(self):
        if not self.textediting: return
        self.text_from_val()
        self.textedit_end()
    
    def release_outside(self, x, y, buttons, modifiers):
        self.textedit_confirm()
        super(UiTextEditControl, self).release_outside(x, y, buttons, modifiers)

class ToggleControl(UiControl):
        
    def press(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.activate()
            self.toggle()
    
    def release(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.deactivate()
    
    def toggle(self):
        self.setval( not self.getval() )
        
        if self.getval():
            col1 = [0.35]*3
            col2 = [0.30]*3
            coltext = [255]*4
        else:
            col1 = [0.5]*3
            col2 = [0.6]*3
            coltext = [0,0,0,255]
            
        self.geo = roundbase(self.x, self.y, self.w, self.h, col1, col2)
        self.label.color = coltext
        
        self.update_draw()

class SliderControl(UiTextEditControl):
    
    def activate(self):
        col1 = [0.3,0.3,0.3]
        col2 = [0.4,0.4,0.4]
        self.geo = roundbase(self.x, self.y, self.w, self.h, col1, col2)
        super(SliderControl, self).activate()
    
    def deactivate(self):
        col1 = [0.5,0.5,0.5]
        col2 = [0.6,0.6,0.6]
        self.geo = roundbase(self.x, self.y, self.w, self.h, col1, col2)
        super(SliderControl, self).deactivate()
    
    def press(self, x, y, buttons, modifiers):
        if self.textediting:
            self.caret.on_mouse_press(x, y, buttons, modifiers)
            return pyglet.event.EVENT_HANDLED
        
        if buttons & pyglet.window.mouse.LEFT:
            self.textedit_begin()
            
        elif buttons & pyglet.window.mouse.MIDDLE:
            self.activate()
    
    def release(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.MIDDLE:
            self.deactivate()
    
    def drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            if self.textediting:
                self.caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
                return pyglet.event.EVENT_HANDLED
        
        if buttons & pyglet.window.mouse.MIDDLE:
            self.setval( self.getval() + dx )
            self.text_from_val()
            self.update_draw()
