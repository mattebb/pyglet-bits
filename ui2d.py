﻿import parameter
import pyglet
from pyglet.gl import *
from pyglet.window import key
from shader import Shader
from ui2ddraw import *
import euclid
import colorsys

class uiGroup(pyglet.graphics.OrderedGroup):
    def __init__(self, order, window, **kwargs):
        super(uiGroup, self).__init__(order, **kwargs)
        self.window = window
        
    def set_state(self):
        width, height = self.window.get_size()

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        glOrtho(0.0, width, 0.0, height, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)

    def unset_state(self):
        glEnable(GL_DEPTH_TEST)
        pass


class uiBlendGroup(uiGroup):
    def set_state(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    def unset_state(self):
        glDisable(GL_BLEND)

class uiShaderGroup(uiGroup):
    
    def __init__(self, order, window, vertex_shader, fragment_shader, **kwargs):
        super(uiShaderGroup, self).__init__(order, window, **kwargs)

        self.shader = Shader(vertex_shader, fragment_shader)

    def set_state(self):
        self.shader.bind()
        #self.shader.uniform_matrixf('projection', camera.matrix * m)
    
    def unset_state(self):
        self.shader.unbind()
        


class UiControls(object):
    
    TOGGLE = 1
    SLIDER = 2
    ACTION = 3

    ANGLE = 1
    
    font_style = {'color': (0, 0, 0, 255),
             'font_size': 8,
             'font_name': 'Bitstream Vera Sans', 
             }

# XXX convert each control to handle itself?
class UiEventHandler(object):
    def __init__(self, window, ui):
        self.window = window
        self.ui = ui

    def on_draw(self):
        if not self.ui.overlay:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.ui.batch.draw()
        self.ui.fps_display.draw()

    def on_expose(self):
        self.on_draw()

    def on_mouse_press(self, x, y, buttons, modifiers):
        for control in [c for c in self.ui.controls if c.point_inside(x, y)]:
            control.on_mouse_press(x, y, buttons, modifiers)

    def on_mouse_release(self, x, y, buttons, modifiers):
        for control in [c for c in self.ui.controls if c.point_inside(x, y)]:
            control.on_mouse_release(x, y, buttons, modifiers)
        
        for control in [c for c in self.ui.controls if c.active 
                                                    and not c.point_inside(x, y)]:
            control.release_outside(x, y, buttons, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        for control in [c for c in self.ui.controls if c.active]:
            control.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
    
    def on_text(self, text):
        for control in [c for c in self.ui.controls if c.active]:
            return control.on_text(text)
    
    def on_key_press(self, symbol, modifiers):
        for control in [c for c in self.ui.controls if c.active]:
            return control.on_key_press(symbol, modifiers)
    
    def on_resize(self, width, height):
        self.ui.layout.reposition(w=width, y=height)
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
    
    def __init__(self, x=10, y=200, w=300, wf=1.0, style=VERTICAL):
        self.style = style
        self.items = []
        self.x = x
        self.y = y
        self.w = w
        self.h = 16
        self.wf = wf
    
    def reposition(self, x=None, y=None, w=None, h=None, wf=None):
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
        if w is not None:
            self.w = w
        if wf is not None:
            self.wf = wf
    
    def layout(self, items=None):
        if items is None:
            items = self.items
            
        y = self.y
        x = self.x
        w = self.w * self.wf

        for i, item in enumerate(items):
            item.x = x
            item.y = y - item.h - 2
            #item.h = self.HEIGHT
            
            if self.style == self.VERTICAL:
                item.w = w
                y = item.y
                #y -= item.h + 2
            elif self.style == self.HORIZONTAL:
                item.w = w / len(items)
                x += item.w

            if type(item) == UiLayout:
                item.layout(item.items)
            
            item.reposition()
    
    def addParameter(self, ui, param, type=None):
        if type is not None:
            controltype = type
        elif param.type in ui.control_types['numeric']:
            controltype = NumericControl
        elif param.type in ui.control_types['toggle']:
            controltype = ToggleControl
        elif param.type in ui.control_types['color']:
            controltype = ColorSwatch

        control = controltype(ui, param=param, vmin=param.min, vmax=param.max)
        self.items.append(control)
        ui.controls.append(control)

        self.layout()

    def addControl(self, ui, **kwargs):
        
        # detect ui control type and length
        
        # attribute controls
        if 'object' in kwargs.keys() and 'attr' in kwargs.keys():
            attr = getattr( kwargs['object'], kwargs['attr'])
            
            if type(attr) in ui.control_types['numeric']:
                controltype = NumericControl
                
            elif type(attr) in ui.control_types['toggle']:
                controltype = ToggleControl

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

    def __init__(self, window, overlay=True):
        self.window = window
        
        self.controls = []
        self.batch = pyglet.graphics.Batch()

        self.overlay = overlay

        self.groups = {}
        self.groups['control'] = uiGroup(3, window)
        self.groups['label'] = uiGroup(10, window, parent=self.groups['control'])
        self.groups['outline'] = uiBlendGroup(5, window, parent=self.groups['control'])
        
        self.groups['wheel'] = uiShaderGroup(3, window, ColorWheel.vertex_shader, ColorWheel.fragment_shader, parent=self.groups['control'])
        
        self.control_types = {}
        self.control_types['numeric'] = [float, int]
        self.control_types['color'] = []
        self.control_types['toggle'] = [bool,]

        self.fps_display = pyglet.clock.ClockDisplay()
        ww, wh = self.window.get_size()
        self.layout = UiLayout(x=10, y=wh, w=ww, wf=0.5 )
        
        self.handler = UiEventHandler(window, self)
        window.push_handlers( self.handler )

    def update(self):
        for control in self.controls:
            control.update()

class UiControl(object):

    LABELSIZE = 0.4

    def __init__(self, ui, x=0, y=0, w=1, h=16, title=''):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.type = type
        
        self.active = False

        self.ui = ui
        self.vertex_lists = {}

        self.title = '' if title is None else title
        
        self.label = pyglet.text.Label(self.title,
                        batch=ui.batch,
                        group=ui.groups['label'],
                        x=0, y=0,
                        **UiControls.font_style )

    def add_shape_geo(self, shapegeo):
        id = shapegeo['id']
        
        # add z dimension to 2d controls
        vertices = np.array(shapegeo['vertices']).reshape(-1,2)
        vertices = np.column_stack( [vertices, np.array([0.0]*len(vertices)) ] )
        
        shapegeo['vertices'] = list(vertices.flat)
        
        if shapegeo['id'] in self.vertex_lists.keys():
            if self.vertex_lists[id].get_size() != shapegeo['len']:
                self.vertex_list.resize(shapegeo['len'])
                
            self.vertex_lists[id].vertices = shapegeo['vertices']
            self.vertex_lists[id].colors = shapegeo['colors']
            if 'tex_coords' in shapegeo.keys():
                self.vertex_lists[id].tex_coords = shapegeo['tex_coords']
            
        else:
            if 'outline' in shapegeo['id']:
                group = self.ui.groups['outline']
            elif 'wheel' in shapegeo['id']:
                group = self.ui.groups['wheel']
            else:
                group = self.ui.groups['control']

            attributes = [('v3f/static', shapegeo['vertices']), \
                          ('c4f/static', shapegeo['colors'])]
            
            if 'tex_coords' in shapegeo.keys():
                attributes.append( ('t2f/static', shapegeo['tex_coords']) )

            self.vertex_lists[id] = self.ui.batch.add( shapegeo['len'], 
                                             shapegeo['mode'],
                                             group,
                                             *attributes)

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

    def on_mouse_press(self, *args, **kwargs):
        self.activate()
        
    def on_mouse_release(self, *args, **kwargs):
        self.deactivate()

    def on_mouse_drag(self, *args, **kwargs):
        pass
    def on_text(self, text):
        pass
    def on_key_press(self, symbol, modifiers):
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
    
    def __init__(self, ui, param=None, object=None, attr='', vmin=0, vmax=100, subtype=None, **kwargs):
        super(UiAttrControl, self).__init__( ui, **kwargs )
        
        self.param = self.object = None
        self.attr = ''

        if param is not None:
            self.param = param
            self.len = param.len
            self.title = param.title if self.title == '' else self.title
        elif hasattr(object, attr):
            self.object = object
            self.attr = attr
            self.len = attr_len(getattr(object, attr))
            self.title = self.attr.capitalize() if self.title == '' else self.title
        else:
            raise ValueError("Invalid attribute provided: %s" % attr)

        self.min = vmin
        self.max = vmax
        self.subtype = subtype
        
        self.label.text = self.title

    def getval(self, sub=None):
        # Parameter interface
        if self.param is not None:
            return self.param.getval(sub=sub)

        # or modify attribute values directly
        attr = getattr(self.object, self.attr)
        if self.len > 1 and sub is not None:
            return attr[sub]
        else:
            return attr
    
    def limited(self, val, newval):
        if type(val) in ('float', 'int'):
            return min(self.max, max(self.min, newval))
        else:
            return newval
    
    def setval(self, newval, sub=None):
        # Parameter interface
        if self.param is not None:
            return self.param.setval(newval, sub=sub)

        # or modify attribute values directly
        attr = getattr(self.object, self.attr)
        if self.len > 1 and sub is not None:
            attr[sub] = self.limited( attr[sub], newval )
        else:
            attr = self.limited(attr, newval)
        
        setattr(self.object, self.attr, attr)


class UiTextEditControl(UiAttrControl):
    
    NUM_VALUE_WIDTH = 56
    
    def __init__(self, ui, **kwargs):
        super(UiTextEditControl, self).__init__( ui, **kwargs)

        self.textediting = None
        
        self.carets = []
        self.documents = []
        self.layouts = []
        for i in range(self.len):
            doc = pyglet.text.document.UnformattedDocument( '' )
            doc.set_style(0, len(doc.text), UiControls.font_style)
            
            layout = pyglet.text.layout.IncrementalTextLayout(
                        doc, 20, 20, multiline=False,
                        batch=ui.batch,
                        group=ui.groups['label'],
                        )
                        
            caret = pyglet.text.caret.Caret(layout)
            caret.visible = False
            
            self.documents.append(doc)
            self.layouts.append(layout)
            self.carets.append(caret)
        
    def update_label(self):
        super(UiTextEditControl, self).update_label()
        
        for i, layout in enumerate(self.layouts):
            w = self.w*(1-self.LABELSIZE) / float(len(self.layouts))
            layout.anchor_y = 'baseline'
            layout.anchor_x = 'left'
            layout.x = int( self.x + self.LABELSIZE*self.w + i*w + 6)
            layout.y = self.y + 4
            layout.width = int( w )
            layout.height = self.h
        
        self.label.width = self.w
        self.label.anchor_x = 'left'
        self.label.x = self.x + 8
        
    
    def val_from_text(self):
        for i, doc in enumerate(self.documents):
            try:
                val = float(doc.text)
                if self.subtype == UiControls.ANGLE:
                    val = math.radians(val)
                self.setval(val, sub=i)
            except:
                pass

    def text_from_val(self):
        for i, doc in enumerate(self.documents):
            val = self.getval(sub=i)
            
            if self.subtype == UiControls.ANGLE:
                doc.text = u"%.2f\xB0" % math.degrees(val) 
            else:
                doc.text = "%.2f" % val

    def textedit_begin(self, s=0):
        self.activate()
        self.textediting = s
        
        self.carets[s].visible = True
        self.carets[s].mark = 0
        self.carets[s].position = len(self.documents[s].text)
        self.update()
    
    def textedit_update(self, text):
        self.carets[self.textediting].on_text(text)
        
    def textedit_end(self):
        self.deactivate()
        self.textediting = None
        for i in range(self.len):
            self.carets[i].visible = False
            self.carets[i].mark = self.carets[i].position = 0
        self.update()
    
    def textedit_confirm(self):
        if self.textediting is None: return
        self.val_from_text()
        self.textedit_end()
    
    def textedit_cancel(self):
        if self.textediting is None: return
        self.textedit_end()
    
    def release_outside(self, x, y, buttons, modifiers):
        self.textedit_confirm()
        super(UiTextEditControl, self).release_outside(x, y, buttons, modifiers)

class ToggleControl(UiAttrControl):
    
    CHECKBOX_W = 10
    CHECKBOX_H = 10
    
    def update_label(self):
        super(ToggleControl, self).update_label()
        self.label.x = self.x + self.CHECKBOX_W + 8

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
    
    def on_mouse_press(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.activate()
            self.toggle()
    
    def on_mouse_release(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.deactivate()
    
    def toggle(self):
        self.setval( not self.getval() )
        self.update()

class PickerWindow(pyglet.window.Window):
    def __init__(self, parentcontrol, *args, **kwargs):
        super(PickerWindow, self).__init__(*args, **kwargs)

        self.parentcontrol = parentcontrol
        self.param = self.parentcontrol.param
        self.parentui = self.parentcontrol.ui

        self.ui = Ui(self, overlay=False)
        self.ui.layout.x = 0
        self.ui.layout.wf = 1.0
        self.ui.layout.addParameter(self.ui, self.param, type=ColorWheel)
        self.ui.layout.addParameter(self.ui, self.param, type=NumericControl)

        glClearColor(0.4, 0.4, 0.4, 1.0)

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        
        if hasattr(self, "ui"):
            self.ui.layout.reposition(w=width, y=height)
            self.ui.layout.layout()

    def update_picker(self):
        self.ui.update()
        self.parentcontrol.update()
        
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.update_picker()
        
    def on_mouse_press(self, x, y, buttons, modifiers):
        self.update_picker()
        

class ColorWheel(UiAttrControl):

    # for all sharing ColorWheel class
    util = ''.join(open('util.glsl').readlines())
    vertex_shader = '''
    void main(void) {
        gl_TexCoord[0]  = gl_MultiTexCoord0;
        gl_FrontColor = gl_Color;
        gl_Position = ftransform();
    }
    '''
    fragment_shader = util + '''
    #define pi 3.141592653589793238462643383279
    vec3 hsvrgb(float h,float s,float v) { return mix(vec3(1.),clamp((abs(fract(h+vec3(3.,2.,1.)/3.)*6.-3.)-1.),0.,1.),s)*v; }

    void main(void) {
        float u = gl_TexCoord[0].s*2.0 - 1.0;
        float v = gl_TexCoord[0].t*2.0 - 1.0;
        float theta = atan(v, u);
        float h = (theta/pi)*0.5 + 0.5;
        float s = sqrt(u*u + v*v);
        float val = gl_Color.x;

        vec4 hsv = vec4(h, s, val, 1.0);
        vec4 rgb = linearrgb_to_srgb( hsv_to_rgb(hsv) );
        gl_FragColor = rgb;
    }
    '''
    
    def __init__(self, *args, **kwargs):
        super(ColorWheel, self).__init__(*args, **kwargs)
        self.h = 128

    def update(self):
        col = self.getval()[:]
        h, s, v = colorsys.rgb_to_hsv(*col)

        self.add_shape_geo( colorwheel(self.x, self.y, self.w, self.h, v) )

    def set_color(self, x, y):
        col = self.getval()[:]
        hue, sat, val = colorsys.rgb_to_hsv(*col)

        r = float(self.h * 0.5)
        cx = self.x + self.w*0.5
        cy = self.y + self.h*0.5

        u = (x - cx) / r
        v = (y - cy) / r

        theta = math.atan2(v, u)
        h = (theta/math.pi)*0.5 + 0.5
        s = math.sqrt(u*u + v*v)

        rgb = parameter.Color3(*colorsys.hsv_to_rgb(h, s, val))

        self.setval(rgb)
        
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.set_color(x, y)

    def on_mouse_press(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.activate()
            self.set_color(x, y)


class ColorSwatch(UiAttrControl):

    def update(self):
        col = list(self.getval())
        col = col + [1.0]
        outline_col = [.2,.2,.2, 1.0]

        w = self.w*(1-self.LABELSIZE)
        x = self.x + self.w*self.LABELSIZE

        self.add_shape_geo( roundbase(x, self.y, w, self.h, 6, col, col) )
        self.add_shape_geo( roundoutline(x, self.y, w, self.h, 6, outline_col) )


    def open_picker(self, x, y):
        wx, wy = self.ui.window.get_location()
        sx, sy = self.ui.window.get_size()

        import platform
        if platform.system() == 'Linux':
            style = pyglet.window.Window.WINDOW_STYLE_DIALOG
        else:
            style = pyglet.window.Window.WINDOW_STYLE_TOOL

        window = PickerWindow(self, 200, 200, \
                                resizable=True, caption='color', style=style)
        window.set_location(wx+x, wy+(sy-y))

    def on_mouse_press(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.open_picker(x, y)

class NumericControl(UiTextEditControl):
    
    def __init__(self, *args, **kwargs):
        super(NumericControl, self).__init__(*args, **kwargs)
        
        self.sliding = None
        
        if self.title == '':
            self.LABELSIZE = 0.0

    def point_inside_sub(self, x, y):
        w = (1-self.LABELSIZE)*self.w / float(self.len)
        offsetx = self.x + self.LABELSIZE*self.w
        
        for i in range(self.len):
            x1 = offsetx + i*w
            x2 = offsetx + (i+1)*w
            if x1 < x < x2 and self.y < y < self.y+self.h:
                return i
        return None

    def update(self):
        self.text_from_val()

        w = (self.w*(1-self.LABELSIZE)) / float(self.len)
        for i in range(self.len):
            if self.active and (self.textediting == i or self.sliding == i):
                col2 = [0.3,0.3,0.3, 1.0]
                col1 = [0.4,0.4,0.4, 1.0]
                outline_col = [.2,.2,.2, 1.0]
                coltext = [255]*4
            else:
                col2 = [0.5,0.5,0.5, 1.0]
                col1 = [0.6,0.6,0.6, 1.0]
                outline_col = [.2,.2,.2, 1.0]
                coltext = [0,0,0,255]

            x = self.x + self.LABELSIZE*self.w + i*w
            x = int(x)
            self.add_shape_geo( roundbase(x, self.y, w, self.h, 6, col1, col2, index=i) )
            self.add_shape_geo( roundoutline(x, self.y, w, self.h, 6, outline_col, index=i) )
        
            self.documents[i].set_style(0, len(self.documents[i].text), {'color': coltext})

    def on_mouse_press(self, x, y, buttons, modifiers):
        s = self.point_inside_sub(x, y)
        if s != None:
            if buttons & pyglet.window.mouse.LEFT:
                if self.textediting == None:
                    self.textedit_begin(s=s)
                elif self.textediting == s:
                    self.carets[s].on_mouse_press(x, y, buttons, modifiers)
                    return pyglet.event.EVENT_HANDLED
                else:
                    self.textedit_end()
                
            elif buttons & pyglet.window.mouse.MIDDLE:
                self.sliding = s
                self.activate()
                
    def on_mouse_release(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.MIDDLE:
            self.deactivate()
    
    def on_text(self, text):
        if self.textediting is not None:
            self.textedit_update(text)
    
    def on_key_press(self, symbol, modifiers):
        if self.textediting is not None:
            if symbol in (key.ENTER, key.RETURN, key.NUM_ENTER):
                self.textedit_confirm()
                return pyglet.event.EVENT_HANDLED
            elif symbol == key.ESCAPE:
                self.textedit_cancel()
                return pyglet.event.EVENT_HANDLED

    def on_mouse_drag_setval(self, dx):
        sensitivity = (self.max - self.min) / 500.0
        self.setval( self.getval(sub=self.sliding) + sensitivity*dx, sub=self.sliding )

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        s = self.point_inside_sub(x, y)
        if s != None:
            if buttons & pyglet.window.mouse.LEFT:
                if self.textediting == s:
                    self.carets[s].on_mouse_drag(x, y, dx, dy, buttons, modifiers)
                    return pyglet.event.EVENT_HANDLED
        
        if buttons & pyglet.window.mouse.MIDDLE:
            if self.sliding is not None:
                self.on_mouse_drag_setval(dx)
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
    
    def on_mouse_press(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.activate()
    
    def on_mouse_release(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.func()
            self.deactivate()

class LabelControl(UiControl):
    def __init__(self, ui, title='', **kwargs):
        self.title = title
        super(LabelControl, self).__init__( ui, **kwargs )
    