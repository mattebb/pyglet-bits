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
from euclid import Vector3, Point3, Matrix4
import pyglet
from pyglet.gl import *
from pyglet.window import mouse, key
from object3d import Object3d
from shader import Shader
from parameter import Parameter


import partio
partio_framecache = {}


glsl_util = ''.join(open('util.glsl').readlines())

from keys import keys

def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    if keys[key.E]:
        if buttons & mouse.LEFT:
            Ptc.exposure.setval( Ptc.exposure.getval() + dx*0.01 )
    if keys[key.Y]:
        if buttons & mouse.LEFT:
            Ptc.gamma.setval( Ptc.gamma.getval() + dx*0.01 )





class Ptc(Object3d):

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
    void main(void) {
        float gain = pow(2.0, exposure);
        vec4 hsv = rgb_to_hsv(gl_Color);
        hsv.r += hueoffset;
        vec4 rgba = hsv_to_rgb(hsv);

        gl_FragColor.r = pow(rgba.r*gain, 1.0/gamma);
        gl_FragColor.g = pow(rgba.g*gain, 1.0/gamma);
        gl_FragColor.b = pow(rgba.b*gain, 1.0/gamma);
    }
    '''
    
    # Class-wide parameters for all class instances
    gamma =     Parameter(default=2.2, vmin=0.0, vmax=3.0, title='Gamma')
    exposure =  Parameter(default=0.0, vmin=-2.0, vmax=2.0, title='Exposure')
    gain =      Parameter(default=1.0, vmin=0.0, vmax=3.0, title='Gain')
    hueoffset = Parameter(default=0.0, vmin=-1.0, vmax=1.0, title='Hue Offset')
    ptsize =    Parameter(default=1.0, vmin=-1.0, vmax=1.0, title='Point Size')

    def __init__(self, scene, filename, *args, **kwargs):
        super(Ptc, self).__init__(scene, *args, **kwargs)

        self.filename = filename
        self.update(scene.time, scene.frame)
        self.vertex_list = self.batch.add(self.numparts,
                                             GL_POINTS,
                                             None,
                                             ('v3f/static', self.vertices),
                                             ('c3f/static', self.colors)
                                             )
        
    def update(self, time, frame, dt=0):
        verts = []
        cols = []
        global partio_framecache

        frame = int(frame)
        #filename = '/jobs/alfx/gatsby/058_dr/058_dr_0060/renders/ryank/ptc/ptc_prop_gDeus_dyn_01Shape/ptc_prop_gDeus_dyn_01Shape.%04d.ptc' % frame
        #filename = '/jobs/alfx/gatsby/058_dr/058_dr_0060/renders/ryank/ptc/ptc_sun_set_static_FG01Shape/ptc_sun_set_static_FG01Shape.ptc'
        filename = self.filename.replace('####', '%04d'%frame)
        
        if filename not in partio_framecache.keys():

            ptc = partio.read(filename)
            print('read ptc %s' % filename)
            if ptc is None:
                self.vertices = []
                self.colors = []
                return
            self.numparts = ptc.numParticles()
            attrs = dict((ptc.attributeInfo(i).name,ptc.attributeInfo(i)) for i in range(ptc.numAttributes()))

            posattr = ptc.attributeInfo(0)
            if 'Cd' in attrs.keys():
                colattr = attrs['Cd']
            elif '_radiosity' in attrs.keys():
                colattr = attrs['_radiosity']

            # if hasattr(ptc, "getNDArray"):
            verts = ptc.getNDArray(posattr)
            cols = ptc.getNDArray(colattr)
            # elif hasattr(ptc, "getArray"):
            #     # using an addition to partio py api
            #     verts = ptc.getArray(posattr)
            #     cols = ptc.getArray(colattr)
            # else:
            #     verts = [ ptc.get(posattr, i) for i in range(numparts)]
            #     cols =  [ ptc.get(colattr, i) for i in range(numparts)]
            #     cols = [item for sublist in cols for item in sublist]   # flatten lists

            # v = np.array(verts).reshape(-1,3)
            #cols = list(cols.flat)
            v = verts.reshape(-1,3)
            self.bbmin = Point3( np.min(v[:,0]), np.min(v[:,1]), np.min(v[:,2]) )
            self.bbmax = Point3( np.max(v[:,0]), np.max(v[:,1]), np.max(v[:,2]) )

            import ctypes
            #partio_framecache[filename] = [list(v.flat) , cols]
            partio_framecache[filename] = [ v.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), cols.ctypes.data_as(ctypes.POINTER(ctypes.c_float)) ]

        self.vertices = partio_framecache[filename][0]
        self.colors = partio_framecache[filename][1]

        if hasattr(self, "vertex_list"):
            self.vertex_list.resize(self.numparts)
            self.vertex_list.vertices = self.vertices
            self.vertex_list.colors = self.colors
            # self.vertex_list.delete()
            # self.vertex_list = self.batch.add(len(self.vertices)//3,
            #                                  GL_POINTS,
            #                                  None,
            #                                  ('v3f/static', self.vertices),
            #                                  ('c3f/static', self.colors)
            #                                  )
            

    def draw(self, time=0, camera=None):
        # stupid rotate_euler taking coords out of order!
        m = Matrix4.new_translate(*self.translate).rotate_euler(*self.rotate.yzx).scale(*self.scale)

        glPointSize(self.ptsize.getval())
        self.shader.bind()
        self.shader.uniformf('gamma', self.gamma.getval())
        self.shader.uniformf('exposure', self.exposure.getval())
        self.shader.uniformf('hueoffset', self.hueoffset.getval())
        self.shader.uniform_matrixf('modelview', camera.matrixinv * m)
        self.shader.uniform_matrixf('projection', camera.persp_matrix)
        
        self.batch.draw()
        self.shader.unbind()