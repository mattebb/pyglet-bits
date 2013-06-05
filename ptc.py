# ##### BEGIN MIT LICENSE BLOCK #####
#
# Copyright (c) 2012 Matt Ebb
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# 
#
# ##### END MIT LICENSE BLOCK #####

import numpy as np
import math
from euclid import Vector3, Point3, Matrix4

import pyglet
from pyglet.gl import *
from pyglet.window import mouse, key
from object3d import Object3d, filename_frame
from shader import Shader
from parameter import Parameter, Histogram
from keys import keys

import ctypes
from ctypes import pointer, sizeof

import os
import partio

glsl_util = ''.join(open('util.glsl').readlines())

tempcache = {}
histogram_cache = {}

class PtcHandler(object):
    ''' Handle user interaction (mouse/keyboard input) '''
    def __init__(self, scene, window):
        self.scene = scene
        self.window = window

    def on_key_press(self, symbol, modifiers):
        if symbol in (pyglet.window.key.LCTRL, pyglet.window.key.RCTRL):
            cursor = self.window.get_system_mouse_cursor(self.window.CURSOR_CROSSHAIR)
            self.window.set_mouse_cursor(cursor)
    def on_key_release(self, symbol, modifiers):
        if symbol in (pyglet.window.key.LCTRL, pyglet.window.key.RCTRL):
            cursor = self.window.get_system_mouse_cursor(self.window.CURSOR_DEFAULT)
            self.window.set_mouse_cursor(cursor)

    def on_mouse_press(self, x, y, buttons, modifiers):
        if buttons & mouse.LEFT and modifiers & key.MOD_CTRL:

            ray = self.scene.camera.project_ray(x, y)
            pts = []
            for ptcloud in self.scene.pointclouds:
                pt = ptcloud.intersect(ray)
                if pt is not None:
                    pts.append( pt )
            if len(pts) == 0: return

            pts.sort(key=lambda x: x[0])
            class BBox(object): pass
            bbox = BBox()
            bbox.bbmin = pts[0] - Vector3(2,2,2)
            bbox.bbmax = pts[0] + Vector3(2,2,2)

            self.scene.camera.focus(bbox)
            return pyglet.event.EVENT_HANDLED
    
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):

        if keys[key.E]:
            if buttons & mouse.LEFT:
                Ptc.exposure.value = Ptc.exposure.value + dx*0.01
                return pyglet.event.EVENT_HANDLED
        if keys[key.Y]:
            if buttons & mouse.LEFT:
                Ptc.gamma.value = Ptc.gamma.value + dx*0.01
                return pyglet.event.EVENT_HANDLED


def valid_file(filename):
    return os.path.exists(filename) and os.path.getsize(filename) > 10000

class Ptc(Object3d):

    # GLSL Shaders below

    vertex_shader = glsl_util+'''
    uniform mat4 modelview;
    uniform mat4 projection;
    varying vec3 normal;
    void main() {
        gl_FrontColor = gl_Color;
        
        vec4 modelSpacePos = modelview * gl_Vertex;
        gl_Position = projection * modelSpacePos;
    }
    '''

    fragment_shader = glsl_util+'''
    uniform float gamma;
    uniform float exposure;
    uniform float hueoffset;
    uniform float decimate;

    void main(void) {
        float gain = pow(2.0, exposure);
        vec4 hsv = rgb_to_hsv(gl_Color);
        hsv.r += hueoffset;
        vec4 rgba = hsv_to_rgb(hsv);

        gl_FragColor.r = pow(rgba.r*gain, 1.0/gamma);
        gl_FragColor.g = pow(rgba.g*gain, 1.0/gamma);
        gl_FragColor.b = pow(rgba.b*gain, 1.0/gamma);
        gl_FragColor.a = 1.0;

        //if (decimate < 1.0) {
        //    float r  = rand(gl_PrimitiveID);
        //    if ( r > decimate) gl_FragColor.a = 0.0;
        // }

    }
    '''
    
    # Class-wide parameters for all class instances
    gamma =     Parameter(default=2.2, vmin=0.0, vmax=3.0, title='Gamma')
    exposure =  Parameter(default=0.0, vmin=-2.0, vmax=2.0, title='Exposure')
    gain =      Parameter(default=1.0, vmin=0.0, vmax=3.0, title='Gain')
    hueoffset = Parameter(default=0.0, vmin=-1.0, vmax=1.0, title='Hue Offset')
    ptsize =    Parameter(default=2.0, vmin=-1.0, vmax=1.0, title='Point Size')

    pos_attrs = ['position']

    # OpenGL Vertex Buffer management
    def init_buffers(self):
        self.vbo_vert_id = GLuint()
        self.vbo_col_id = GLuint()
        glGenBuffers(1, pointer(self.vbo_vert_id))
        glGenBuffers(1, pointer(self.vbo_col_id))

    def update_buffers(self):
        if not hasattr(self, "verts"): return
        self.vbo_vert_data = self.verts.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vert_id)
        glBufferData(GL_ARRAY_BUFFER, sizeof(ctypes.c_float)*len(self.verts), self.vbo_vert_data, GL_STATIC_DRAW)

        if not hasattr(self, "cols"): return
        self.vbo_col_data = self.cols.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_col_id)
        glBufferData(GL_ARRAY_BUFFER, sizeof(ctypes.c_float)*len(self.cols), self.vbo_col_data, GL_STATIC_DRAW)

    def delete_buffers(self):
        glDeleteBuffers(1, self.vbo_vert_id)
        glDeleteBuffers(1, self.vbo_col_id)

    def update_visibility(self):
        if self.visible.value == False:
            self.delete_buffers()
        elif self.visible.value == True:
            if not glIsBuffer(self.vbo_vert_id) and not glIsBuffer(self.vbo_col_id):
                self.init_buffers()
            self.update_buffers()

    def __init__(self, scene, filepath, *args, **kwargs):
        super(Ptc, self).__init__(scene, *args, **kwargs)

        self.visible = Parameter(default=True, title='Visible', update=self.update_visibility)
        self.filepath = filepath
        self.filename = ''  # after frame conversion
        self.frame = None
        self.vbo_vert_data = None
        self.vbo_col_data = None
        self.ptc_loaded = False

        # object-specific parameters
        self.decimate = Parameter(default=1.0, vmin=0.0, vmax=1.0, title='Decimate')
        self.num_particles = Parameter(default=0, title='Num particles: ')
        self.attributes = Parameter(default='', title='', update=self.read_ptc_attrs_data)
        self.attr_stats = Parameter(default='', title='')
        self.histogram = Parameter(default=Histogram(), title='')
        self.show_statistics = Parameter(default=True, title='Update Stats')
        
        # create VBOs
        self.init_buffers()

        # load ptc, store in self.verts/self.cols, update VBOs if loaded
        self.frame = scene.frame.value
        self.read_ptc_attrs_data()


    def read_ptc_attrs_data(self):
        ptc = self.open_ptc()

        # init attribute list from ptc
        self.attributes.enum = [ (i, i) for i in self.attrs.keys() if i not in self.pos_attrs ]

        self.read_ptc_data(ptc)
        self.update_buffers()

    def read_partio(self, filename):
        if filename[-7:] == '.pdb.gz':
            global tempcache
            import tempfile
            import gzip

            if filename in tempcache.keys():
                ptc = partio.read(tempcache[filename].name)
            else:
                tmpf = tempfile.NamedTemporaryFile(suffix='.pdb32')
                gzf = gzip.open(filename)
                tmpf.write(gzf.read())
                gzf.close()
                ptc = partio.read(tmpf.name)
                
                tempcache[filename] = tmpf
                # tmpf.close()  # python will close and remove temp files on exit

        else:
            ptc = partio.read(filename)

        return ptc

    def open_ptc(self):
        '''Open a partio point cloud and retrieve attribute info'''
        
        self.filename = filename_frame(self.filepath, self.frame)
        if not valid_file(self.filename):
            return None
            
        ptc = self.read_partio(self.filename)
        if ptc is None: return None

        # Retrieve attribute info
        self.numparts = ptc.numParticles()
        self.num_particles.value = self.numparts
        self.attrs = {}
        for i in range(ptc.numAttributes()):
            self.attrs[ptc.attributeInfo(i).name] = ptc.attributeInfo(i)

        return ptc

    def calc_attribute_stats(self, attr_array, count, attr_name):
        if self.show_statistics.value:

            if count == 3:
                a = attr_array.reshape(-1,3)
                self.attr_stats.value = 'Min:  %.3f %.3f %.3f \nMax: %.3f %.3f %.3f \nAvg:  %.3f %.3f %.3f' % \
                    (a[:,0].min(), a[:,1].min(), a[:,2].min(), \
                    a[:,0].max(), a[:,1].max(), a[:,2].max(), \
                    a[:,0].mean(), a[:,1].mean(), a[:,2].mean() )

                if self.filename+attr_name in histogram_cache.keys():
                    self.histogram.value = histogram_cache[self.filename+attr_name]
                else:
                    histogram = Histogram()
                    for i in range(3):
                        h, bins = np.histogram(a[:,i], bins=64, new=True)
                        if attr_name in ('Cd', '_radiosity'):
                            h = np.power(h, 1/2.2)  # force gamma 2.2 in histogram for colours
                        hist = np.column_stack((bins[1:], h))
                        histogram.arrays.append( hist )
                    self.histogram.value = histogram
                    histogram_cache[self.filename+attr_name] = self.histogram.value

            elif count == 1:
                a = attr_array
                self.attr_stats.value = 'Min:  %.3f \nMax: %.3f \nAvg:  %.3f' % \
                    (a.min(), a.max(), a.mean())

                if self.filename+attr_name in histogram_cache.keys():
                    self.histogram.value = histogram_cache[self.filename+attr_name]
                else:
                    h, bins = np.histogram(a, bins=64)
                    hist = np.column_stack((bins[1:], h))   # somethign nicer for the bins?
                    histogram = Histogram()
                    histogram.arrays = [hist]
                    self.histogram.value = histogram
                    histogram_cache[self.filename+attr_name] = self.histogram.value
            else:
                self.attr_stats.value = ''

        else:
            self.attr_stats.value = ''
            self.histogram.value = Histogram()


    def read_ptc_data(self, ptc):
        '''Read point cloud data into numpy arrays '''

        if ptc is None: return

        if 'position' in self.attrs.keys():
            posattr = self.attrs['position']

        colattr = None
        userattr = self.attributes.value
        if userattr != '' and userattr in self.attrs.keys():
            colattr = self.attrs[userattr]
            aname = userattr
        else:
            if 'Cd' in self.attrs.keys():
                aname = 'Cd'
            elif '_radiosity' in self.attrs.keys():
                aname = '_radiosity'
            elif 'velocity' in self.attrs.keys():
                aname = 'velocity'
            colattr = self.attrs[aname]
            self.attributes.data = aname    # XXX bypassing update function.. needs better implementation

        # load position and colour data
        if hasattr(ptc, "getArray"):  # using an addition to partio py api
            self.verts = ptc.getArray(posattr)
            if colattr is not None:
                cols = ptc.getArray(colattr)
        else:
            self.verts = np.array([ ptc.get(posattr, i) for i in range(self.numparts)])
            if colattr is not None:
                cols = np.array([ ptc.get(colattr, i) for i in range(self.numparts)])
        del ptc

        self.cols = cols.repeat(3) if colattr.count == 1 else cols
        self.ptc_loaded = True

        # calculate bbox min and max
        v = self.verts.reshape(-1,3)
        self.bbmin = Point3( np.min(v[:,0]), np.min(v[:,1]), np.min(v[:,2]) )
        self.bbmax = Point3( np.max(v[:,0]), np.max(v[:,1]), np.max(v[:,2]) )

        self.calc_attribute_stats(cols, colattr.count, aname)

        
    def update(self, time, frame, dt=0):
        self.frame = int(frame)
        self.read_ptc_attrs_data()


    def intersect(self, ray):
        """
        Intersect a ray with a point cloud.
        
        Find the points within a specified angle threshold 
        between the ray vector and the vector ray origin->point
        and take the closest point from that list
        """
        dot_thresh = math.cos(math.radians(1))  # 1 degree angle
        verts = self.verts.reshape(-1,3)
        
        # vector ray origin to point
        rayp = np.array(ray.p[:]).reshape(-1,3).repeat(len(verts), axis=0)
        v = verts - rayp
        # normalise
        v_length = np.sqrt((v ** 2).sum(1)).reshape(-1,1)
        v /= v_length
        # dot product (vector to point . ray vector)
        d = (v * np.array(ray.v)).sum(1)
        
        # boolean array representing where dot > 0.99
        condition = (d > dot_thresh).reshape(-1,1)
        
        # filtered selection where condition is true
        verts_within_angle = verts[condition.repeat(3, axis=1)].reshape(-1,3)
        v_len_within_angle = v_length[condition]

        if len(verts_within_angle) == 0:
            return None

        # sort verts within angle based on ordering of distance to ray origin
        sort_order = v_len_within_angle.argsort()
        ordered_verts = verts_within_angle[sort_order]
        
        l = ordered_verts[0].tolist()
        
        return Vector3(*l)

    def draw(self, time=0, camera=None):
        if not self.visible.value or not self.ptc_loaded:
            return

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # bind glsl uniforms
        glPointSize(self.ptsize.value)
        self.shader.bind()
        self.shader.uniformf('gamma', self.gamma.value)
        self.shader.uniformf('exposure', self.exposure.value)
        self.shader.uniformf('hueoffset', self.hueoffset.value)
        self.shader.uniformf('decimate', self.decimate.value)
        self.shader.uniform_matrixf('modelview', camera.matrixinv * self.matrix())
        self.shader.uniform_matrixf('projection', camera.persp_matrix)
        
        # bind and draw vertex buffers
        glEnableClientState(GL_VERTEX_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vert_id)
        glVertexPointer(3, GL_FLOAT, 0, 0)

        glEnableClientState(GL_COLOR_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_col_id)
        glColorPointer(3, GL_FLOAT, 0, 0)

        glDrawArrays( GL_POINTS, 0, self.numparts )

        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)

        self.shader.unbind()

        glDisable(GL_BLEND)