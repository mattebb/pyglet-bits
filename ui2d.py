import pyglet
from pyglet.gl import *
from pyglet.window import key
from ui2ddraw import *
import euclid

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
        
        glDisable(GL_DEPTH_TEST);

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
    
    def on_resize(self, width, height):
        self.ui.layout.reposition(w=int(width*0.35), h=height)
        self.ui.layout.layout()

def attr_len(attr):
    # if attr is subscriptable
    if hasattr(attr, "__getitem__"):
        return len(attr)
    else:
        return 1

class UiLayout(object):
    
    VERTICAL = 1
    HORIZONTAL = 2
    CONTROL = 3

    HEIGHT = 16
    
    def __init__(self, style=VERTICAL):
        self.style = style
        self.items = []
        self.x = 10
        self.y = 200
        self.w = 300
    
    def reposition(self, x=None, y=None, w=None, h=None):
        if x is not None:
            self.x = x
        if y is not None:
            self.y = h
        if w is not None:
            self.w = w
    
    def layout(self, items=None):
        if items is None:
            items = self.items
            
        y = self.y
        x = self.x
        for i, item in enumerate(items):
            item.x = x
            item.y = y
            item.h = self.HEIGHT
            
            if self.style == self.VERTICAL:
                item.w = self.w
                y -= self.HEIGHT + 2
            elif self.style == self.HORIZONTAL:
                item.w = self.w / len(items)
                x += item.w
            '''
            elif self.style == self.CONTROL:
                label = int(self.w * 0.4)
                ctrl = (self.w - label) / (len(items)-1)
                if i == 0:
                    item.w = label
                else:
                    item.w = ctrl
                x += item.w
            '''

            if type(item) == UiLayout:
                item.layout(item.items)
            
            item.reposition()

    def SliderTemplate(self, ui, **kwargs):
        # split multi-element attribute into several ui controls

        ### Clean up usage of ui/controls - should process layout rather than ui.controls

        layout = UiLayout(style=UiLayout.CONTROL)
        label = LabelControl(ui, title=kwargs['attr'].capitalize())
        layout.items.append(label)

        attr = getattr( kwargs['object'], kwargs['attr'])
            
        
        if attr_len(attr) is None:
            control = SliderControl(ui, title='', **kwargs)
            layout.items.append(control)
            ui.controls.append(control)
        else:
            for i in range(attr_len(attr)):
                control = SliderControl(ui, title='', element=i, **kwargs)
                layout.items.append(control)
                ui.controls.append(control)

        return layout

    
    def addControl(self, ui, **kwargs):
        
        # detect ui control type and length
        
        # attribute controls
        if 'object' in kwargs.keys() and 'attr' in kwargs.keys():
            attr = getattr( kwargs['object'], kwargs['attr'])
            
            #alen = attr_len(attr)
            
            if type(attr) in (float, int, euclid.Point3, euclid.Vector3):
                controltype = SliderControl
                #layoutstyle = UiLayout.CONTROL
                
            elif type(attr) in (bool,):
                controltype = ToggleControl
                #layoutstyle = UiLayout.HORIZONTAL

            #templatelayout = self.SliderTemplate(ui, **kwargs)
            control = controltype(ui, **kwargs)
            self.items.append(control)
            ui.controls.append(control)

        # action control
        elif 'func' in kwargs.keys():
            control = ActionControl(ui, **kwargs)
            self.items.append(control)
            ui.controls.append(control)
        
        self.layout()

class Ui(object):

    def __init__(self, window):
        self.window = window
        self.controls = []
        self.batch = pyglet.graphics.Batch()
        self.control_group = uiGroup(3, window)
        self.control_outline_group = uiBlendGroup(5, window, parent=self.control_group)
        self.control_label_group = uiGroup(10, window, parent=self.control_group)
        
        self.layout = UiLayout()
        
        ui_handlers = UiEventHandler(window, self)
        window.push_handlers(ui_handlers)

class UiControl(object):
    def __init__(self, ui, x=0, y=0, w=1, h=1, title=''):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.type = type
        
        self.active = False
        self.textediting = False

        self.ui = ui
        self.vertex_lists = {}

        self.title = '' if title is None else title
        
        self.label = pyglet.text.Label(self.title,
                        batch=ui.batch,
                        group=ui.control_label_group,
                        x=0, y=0,
                        **UiControls.font_style )

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
        self.label.x = self.x+8
        self.label.y = self.y+4
        self.label.height = self.h

    def reposition(self):
        self.update_label()
        self.update()

    def update(self):
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
        self.update()
    def deactivate(self):
        self.active = False
        self.update()
        

class UiAttrControl(UiControl):
    
    def __init__(self, ui, object=None, attr='', vmin=0, vmax=100, **kwargs):
        super(UiAttrControl, self).__init__( ui, **kwargs )

        self.object = object
        if hasattr(object, attr):
            self.attr = attr
        else:
            raise ValueError("Invalid attribute provided: %s" % attr)

        self.len = attr_len(getattr(object, attr))
        #self.element = element
        self.min = vmin
        self.max = vmax
        
        if self.title == '':
            self.title = self.attr.capitalize()
        self.label.text = self.title        

    def getval(self, sub=None):
        attr = getattr(self.object, self.attr)
        
        #if self.element is not None:
        #    return attr[self.element]
        #else:
        #    return attr

        if sub is not None:
            return attr[sub]
        else:
            return attr
        #return attr
    
    def limited(self, val, newval):
        if type(val) in ('float', 'int'):
            return min(self.max, max(self.min, newval))
        else:
            return newval
    
    def setval(self, newval, sub=None):
        attr = getattr(self.object, self.attr)
        
        #if self.element is not None:
        #    attr[self.element] = self.limited( attr[self.element], newval )
        #else:
        #    attr = self.limited(attr, newval)

        #attr = self.limited(attr, newval)

        if sub is not None:
            attr[sub] = self.limited( attr[sub], newval )
        else:
            attr = self.limited(attr, newval)
        
        
        setattr(self.object, self.attr, attr)


class UiTextEditControl(UiAttrControl):
    
    NUM_VALUE_WIDTH = 56
    
    def __init__(self, ui, **kwargs):
        super(UiTextEditControl, self).__init__( ui, **kwargs)

        self.document = pyglet.text.document.UnformattedDocument( '' )
        self.document.set_style(0, len(self.document.text), UiControls.font_style)

        self.layout = pyglet.text.layout.IncrementalTextLayout(
                        self.document, 20, 20, multiline=False,
                        batch=ui.batch,
                        group=ui.control_label_group,
                        )
        '''
        for i in range(self.len):
            layout = pyglet.text.layout.IncrementalTextLayout(
                        self.document, 20, 20, multiline=False,
                        batch=ui.batch,
                        group=ui.control_label_group,
                        )
            self.layouts.append( layout )
        '''
        self.caret = pyglet.text.caret.Caret(self.layout)
        self.caret.visible = False
        
        self.text_from_val()
    
    def update_label(self):
        super(UiTextEditControl, self).update_label()
        
        self.layout.anchor_y = 'baseline'
        self.layout.anchor_x = 'right'
        self.layout.x = self.x + self.w - 4
        self.layout.y = self.y + 4
        self.layout.width = self.w
        self.layout.height = self.h
        
        self.label.width = self.w
        self.label.anchor_x = 'left'
        self.label.x = self.x + 8
        
    
    def val_from_text(self):
        try:
            val = float(self.document.text)
            self.setval(val)
        except:
            pass

    def text_from_val(self):
        return
        #self.document.text = " %.2f" % self.getval()

    def textedit_begin(self):
        self.activate()

        self.textediting = True
        self.caret.visible = True
        self.caret.mark = 0
        self.caret.position = len(self.document.text)
        self.update()

    def textedit_update(self, text):
        self.caret.on_text(text)
        self.update()
        
    def textedit_end(self):
        self.deactivate()
        self.textediting = False
        self.caret.visible = False
        self.caret.mark = self.caret.position = 0
        self.update()
    
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
    
    CHECKBOX_W = 7
    CHECKBOX_H = 9
    
    def update_label(self):
        super(ToggleControl, self).update_label()
        self.label.x = self.x + self.CHECKBOX_W*2 + 2

    def update(self):
        
        if self.getval():
            col1 = [0.35]*3 + [1.0]
            col2 = [0.30]*3 + [1.0]
            coltext = [255]*4
            outline_col = [.2,.2,.2, 1.0]
            checkmark_col = [1,1,1,1.0]
        else:
            col2 = [0.5]*3 + [1.0]
            col1 = [0.6]*3 + [1.0]
            coltext = [0,0,0,255]
            outline_col = [.25,.25,.25, 1.0]
            checkmark_col = [0,0,0,0.0]
        
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
        self.update()

class SliderControl(UiTextEditControl):

    def point_inside_sub(self, x, y):
        return

    def drag_setval(self, dx):
        sensitivity = (self.max - self.min) / 500.0
        self.setval( self.getval() + sensitivity*dx )

    def update(self):
        if self.active:
            col2 = [0.3,0.3,0.3, 1.0]
            col1 = [0.4,0.4,0.4, 1.0]
            outline_col = [.2,.2,.2, 1.0]
            coltext = [255]*4
        else:
            col2 = [0.5,0.5,0.5, 1.0]
            col1 = [0.6,0.6,0.6, 1.0]
            outline_col = [.2,.2,.2, 1.0]
            coltext = [0,0,0,255]
        
        w = (self.w*0.7) / float(self.len)
        for i in range(self.len):
            x = self.x + 0.3*self.w + i*w
            x = int(x)
            self.add_shape_geo( roundbase(x, self.y, w, self.h, 6, col1, col2, index=i) )
            self.add_shape_geo( roundoutline(x, self.y, w, self.h, 6, outline_col, index=i) )
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
            if self.active:
                self.drag_setval(dx)
                self.text_from_val()
                self.update()

class ActionControl(UiControl):
    
    def __init__(self, ui, object=None, attr='', func=None, **kwargs):
        super(ActionControl, self).__init__( ui, **kwargs )

        if func is None:
            raise ValueError('Invalid function')
        self.func = func
        if self.title == '':
            self.title = self.func.__name__.capitalize()
        self.label.text = self.title
        
    
    def update_label(self):
        super(ActionControl, self).update_label()
        self.label.anchor_x = 'center'
        self.label.x = self.x + self.w//2
        

    def update(self):
        
        if self.active:
            col1 = [0.35]*3 + [1.0]
            col2 = [0.30]*3 + [1.0]
            outline_col = [.2,.2,.2, 1.0]
            coltext = [255]*4
        else:
            col1 = [0.5]*3 + [1.0]
            col2 = [0.6]*3 + [1.0]
            outline_col = [.25,.25,.25, 1.0]
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

class LabelControl(UiControl):
    def __init__(self, ui, title='', **kwargs):
        self.title = title
        super(LabelControl, self).__init__( ui, **kwargs )
    