import pyglet
from pyglet.gl import *
from pyglet.window import key
from ui2ddraw import *

class uiGroup(pyglet.graphics.OrderedGroup):
    def __init__(self, order, window, **kwargs):
        super(uiGroup, self).__init__(order, **kwargs)
        self.window = window
        
    def set_state(self):
        winsize = self.window.get_size()
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        glOrtho(0.0, winsize[0], 0.0, winsize[1], -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        #glTranslatef(0.375, 0.375, 0.0)
        
        #glDisable(GL_DEPTH_TEST);

    def unset_state(self):
        pass

class uiBlendGroup(uiGroup):
    def __init__(self, order, window, parent=None):
        super(uiBlendGroup, self).__init__(order, window, parent=parent)
    
    def set_state(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    def unset_state(self):
        glDisable(GL_BLEND)


class UiControls(object):
    
    TOGGLE = 1
    SLIDER = 2
    ACTION = 3
    
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
        self.control_group = uiGroup(2, window)
        self.control_outline_group = uiBlendGroup(5, window, parent=self.control_group)
        self.control_label_group = uiGroup(10, window, parent=self.control_group)
        
        ui_handlers = UiEventHandler(window, self)
        window.push_handlers(ui_handlers)

    def addControl(self, type=None, **kwargs):
        if type == UiControls.SLIDER:
            self.controls.append( SliderControl( 10, 30, 120, 16, self, **kwargs ) )
            
        elif type == UiControls.TOGGLE:
            self.controls.append( ToggleControl( 10, 10, 120, 16, self, **kwargs ) )
            
        else:
            self.controls.append( ActionControl( 10, 50, 120, 16, self, **kwargs ) )


class UiControl(object):
    def __init__(self, x, y, w, h, ui, object=None, attr='', vmin=0, vmax=100):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.type = type
        
        self.active = False
        self.textediting = False

        self.ui = ui
        self.vertex_lists = {}
        
        self.label = pyglet.text.Label(self.title,
                        batch=ui.batch,
                        group=ui.control_label_group,
                        x=x+8, y=y+4,
                        **UiControls.font_style)
        
        self.update_label()
        self.update_draw()

    def add_shape_geo(self, shapegeo):
        id = shapegeo['id']
        
        if shapegeo['id'] in self.vertex_lists.keys():
            if self.vertex_lists[id].get_size() != shapegeo['len']:
                self.vertex_list.resize(shapegeo['len'])
                
            self.vertex_lists[id].vertices = shapegeo['vertices']
            self.vertex_lists[id].colors = shapegeo['colors']
            
        else:
            if 'outline' in shapegeo['id']:
                group = self.ui.control_outline_group
            else:
                group = self.ui.control_group
            self.vertex_lists[id] = self.ui.batch.add( shapegeo['len'], 
                                             shapegeo['mode'],
                                             group,
                                             ('v2f/static', shapegeo['vertices']),
                                             ('c4f/static', shapegeo['colors'])
                                             )

    def point_inside(self, x, y):
        if x < self.x:          return False
        if x > self.x+self.w:   return False
        if y < self.y:          return False
        if y > self.y+self.h:   return False
        return True

    def delete(self):
        for v in self.vertex_lists.values():
            v.delete()
    
    # override in subclasses
    def update_label(self):
        self.label.anchor_y = 'baseline'
        self.label.height = self.h

    def update_draw(self):
        pass

    def press(self, *args, **kwargs):
        pass
    def release(self, *args, **kwargs):
        pass
    def drag(self, *args, **kwargs):
        pass
    def release_outside(self, x, y, buttons, modifiers):
        self.deactivate()

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
        

class UiAttrControl(UiControl):
    
    def __init__(self, x, y, w, h, ui, object=None, attr='', vmin=0, vmax=100, **kwargs):
        
        self.object = object
        if hasattr(object, attr):
            self.attr = attr
        else:
            raise ValueError("Invalid attribute provided: %s" % attr)

        self.min = vmin
        self.max = vmax
        
        self.title = self.attr.capitalize()
        
        super(UiAttrControl, self).__init__( x, y, w, h, ui, **kwargs )

    def getval(self):
        return getattr(self.object, self.attr)
    def setval(self, newval):
        setattr(self.object, self.attr, min(self.max, max(self.min, newval )) )


class UiTextEditControl(UiAttrControl):
    
    NUM_VALUE_WIDTH = 56
    
    def __init__(self, x, y, w, h, ui, **kwargs):
        self.document = pyglet.text.document.UnformattedDocument( '' )
        self.document.set_style(0, len(self.document.text), UiControls.font_style)

        self.layout = pyglet.text.layout.IncrementalTextLayout(
                        self.document, w, h, multiline=False,
                        batch=ui.batch,
                        group=ui.control_label_group,
                        )
        self.caret = pyglet.text.caret.Caret(self.layout)
        self.caret.visible = False
        
        self.layout.anchor_y = 'baseline'
        self.layout.x = x + w - self.NUM_VALUE_WIDTH + 4
        self.layout.y = y + 4
        
        
        super(UiTextEditControl, self).__init__( x, y, w, h, ui, **kwargs)
        
        self.label.width = self.NUM_VALUE_WIDTH
        self.label.anchor_x = 'right'
        self.label.x = self.x + self.w - self.NUM_VALUE_WIDTH - 8
        
        self.text_from_val()

    
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

class ToggleControl(UiAttrControl):
    
    CHECKBOX_W = 8
    CHECKBOX_H = 9
    
    def update_label(self):
        self.label.x = self.x + self.CHECKBOX_W*2 + 2

    def update_draw(self):
        
        if self.getval():
            col1 = [0.35]*3 + [1.0]
            col2 = [0.30]*3 + [1.0]
            coltext = [255]*4
            outline_col = [.1,.1,.1, .5]
            checkmark_col = [0.1,0.1,0.1,1.0]
        else:
            col2 = [0.5]*3 + [1.0]
            col1 = [0.6]*3 + [1.0]
            coltext = [0,0,0,255]
            outline_col = [.2,.2,.2, 0.5]
            checkmark_col = [0.1,0.1,0.1,0.0]
        
        cbw = self.CHECKBOX_W
        cbh = self.CHECKBOX_H
        cbx = self.x + 2
        cby = self.y + (self.h - cbh)*0.5
        
        self.add_shape_geo( roundbase(cbx, cby, cbw, cbh, 2, col1, col2) )
        self.add_shape_geo( roundoutline(cbx, cby, cbw, cbh, 2, outline_col) )
        self.add_shape_geo( checkmark(cbx, cby, cbw, cbh, checkmark_col) )
        self.label.color = coltext
    
    def press(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.activate()
            self.toggle()
    
    def release(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.deactivate()
    
    def toggle(self):
        self.setval( not self.getval() )
        self.update_draw()

class SliderControl(UiTextEditControl):

    def update_draw(self):
        if self.active:
            col2 = [0.3,0.3,0.3, 1.0]
            col1 = [0.4,0.4,0.4, 1.0]
            outline_col = [.1,.1,.1, .5]
            coltext = [255]*4
        else:
            col2 = [0.5,0.5,0.5, 1.0]
            col1 = [0.6,0.6,0.6, 1.0]
            outline_col = [.3,.3,.3, 0.5]
            coltext = [0,0,0,255]
    
        w = self.NUM_VALUE_WIDTH
        x = self.x + self.w - w
    
        self.add_shape_geo( roundbase(x, self.y, w, self.h, 6, col1, col2) )
        self.add_shape_geo( roundoutline(x, self.y, w, self.h, 6, outline_col) )
        self.document.set_style(0, len(self.document.text), {'color': coltext})

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

class ActionControl(UiControl):
    
    def __init__(self, x, y, w, h, ui, object=None, attr='', func=None, **kwargs):
        
        if func is None:
            raise ValueError('Invalid function')
        self.func = func
        self.title = self.func.__name__.capitalize()
        
        super(ActionControl, self).__init__( x, y, w, h, ui, **kwargs )
    
    def update_label(self):
        self.label.anchor_x = 'center'
        self.label.x = self.x + self.w//2

    def update_draw(self):
        
        if self.active:
            col1 = [0.35]*3 + [1.0]
            col2 = [0.30]*3 + [1.0]
            outline_col = [.1,.1,.1, .5]
            coltext = [255]*4
        else:
            col1 = [0.5]*3 + [1.0]
            col2 = [0.6]*3 + [1.0]
            outline_col = [.3,.3,.3, 0.5]
            coltext = [0,0,0,255]
            
        self.add_shape_geo( roundbase(self.x, self.y, self.w, self.h, 6, col1, col2) )
        self.add_shape_geo( roundoutline(self.x, self.y, self.w, self.h, 6, outline_col) )
        self.label.color = coltext
    
    def press(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.activate()
    
    def release(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.func()
            self.deactivate()
