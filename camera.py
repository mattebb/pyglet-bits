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

import platform
import math
from math import pi, sin, cos

import euclid
from euclid import Vector3, Point3, Matrix4, Ray3

import pyglet
from pyglet.window import key
from pyglet.window import mouse
from pyglet.gl import *

from keys import keys

class CameraHandler(object):
    def __init__(self, window, camera):
        self.camera = camera
        self.window = window
        
        window.push_handlers(keys)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        
        if platform.system() != 'Darwin':
            dy = -dy

        if keys[key.SPACE] or modifiers & pyglet.window.key.MOD_ALT:
            if buttons & mouse.LEFT:
                s = 0.0075
                m = self.camera.matrix
                mi = self.camera.matrixinv
                globaly = Vector3(*mi[4:7])

                xaxis = Vector3(1,0,0)
                d = abs(Vector3(*m[12:15]) - self.camera.center)
                offs = Vector3(0,0,d)

                m *= Matrix4.new_translate(*(-offs)).rotate_axis(s*-dx, globaly).rotate_axis(s*-dy, xaxis).translate(*(offs))
                
            if buttons & mouse.RIGHT:
                s = -0.05

                m = self.camera.matrix
                dist = (Point3(*m[12:15]) - self.camera.center) * 0.1
                # dist = abs(dist)

                zaxis = Vector3(0,0,1)
                tx = zaxis*s*dx + zaxis*s*dx*dist
                m.translate(*tx)
                #self.camera.center -= zaxis*s*dx

            
            if buttons & mouse.MIDDLE:
                s = -0.01
                m = self.camera.matrix

                dist = (Point3(*m[12:15]) - self.camera.center) * 0.3
                dist = abs(dist)

                xaxis = Vector3(1,0,0)
                yaxis = Vector3(0,1,0)
                trans = Matrix4.new_translate(*(xaxis*s*dx*dist)).translate(*(yaxis*s*-dy*dist))

                m *= trans
                self.camera.center = trans * self.camera.center

            self.camera.update()

    def on_resize(self, width, height):
        self.camera.view_update(width, height)


class Camera(object):

    def update_projection(self):
        width, height = self.window.get_size()
        self.persp_matrix = Matrix4.new_perspective(self.fov, width / float(height), self.clipnear, self.clipfar)

    def update(self):
        self.matrixinv = self.matrix.inverse()

    def focus(self, ob):
        if not (hasattr(ob, "bbmin") and hasattr(ob, "bbmax")):
            return
        if ob.bbmin is None or ob.bbmax is None: 
            return

        diam = ob.bbmax - ob.bbmin
        newcenter = ob.bbmin + diam*0.5
        offset = newcenter - self.center

        dist = (abs(diam)*0.5) / math.tan(self.fov*0.5)

        self.center = newcenter
        m = self.matrix
        m[12:15] = self.center
        self.matrix.translate(0,0,dist)

        self.update()

    def __init__(self, window):
        self.fov = math.radians(50)
        self.clipnear = 0.1
        self.clipfar = 100000
        
        self.needs_update = True
        
        self.params = {}
        
        self.window = window
        handlers = CameraHandler(window, self)
        window.push_handlers(handlers)
        
        self.center = Point3(0,0,0)
        self.matrix = Matrix4().new_rotate_axis(math.pi*-0.1, Vector3(1,0,0)).translate(0,0.0,6)
        self.matrixinv = self.matrix.inverse()
        self.persp_matrix = Matrix4()

    @property
    def location(self):
        return Point3(*self.matrix[12:15])

    def project_ray(self, px, py):

        # cam_view = (self.center - self.location).normalize()
        # self.cam_h =  cam_view.cross(self.up).normalize()
        # self.cam_v = -1 * cam_view.cross(self.cam_h).normalize()

        view = -Vector3(*self.matrix[8:11])
        h = Vector3(*self.matrix[0:3])
        v = Vector3(*self.matrix[4:7])
        
        half_v = math.tan(self.fov)*0.5 * self.clipnear
        win = self.window.get_size()
        aspect = win[0] / float(win[1])
        half_h = half_v * aspect
        
        # mouse to ndc
        nx = (px - win[0]*0.5) / (win[0]*0.5)
        ny = (py - win[1]*0.5) / (win[1]*0.5)
        
        h *= half_h
        v *= half_v

        click = self.location + (view*self.clipnear)  + (nx * h) + (ny * v)

        dir = (click - self.location).normalize()
        return Ray3(click, dir)
    
    def view_update(self, width, height):
        glViewport(0, 0, width, height)
        
        # match openGL format
        self.persp_matrix = Matrix4.new_perspective(self.fov, width / float(height), self.clipnear, self.clipfar)

        
        
