#!/usr/bin/env python
# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

'''Displays a rotating torus using the pyglet.graphics API.

This example is very similar to examples/opengl.py, but uses the
pyglet.graphics API to construct the indexed vertex arrays instead of
using OpenGL calls explicitly.  This has the advantage that VBOs will
be used on supporting hardware automatically.  

The vertex list is added to a batch, allowing it to be easily rendered
alongside other vertex lists with minimal overhead.
'''

from math import pi, sin, cos
import random

import pyglet
from pyglet.gl import *

try:
    # Try and create a window with multisampling (antialiasing)
    config = Config(sample_buffers=1, samples=4, depth_size=16, double_buffer=True,)
    window = pyglet.window.Window(resizable=True, config=config)
except pyglet.window.NoSuchConfigException:
    # Fall back to no multisampling for old hardware
    window = pyglet.window.Window(resizable=True)

@window.event
def on_resize(width, height):
    # Override the default on_resize handler to create a 3D projection
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60., width / float(height), .1, 1000.)
    glMatrixMode(GL_MODELVIEW)
    return pyglet.event.EVENT_HANDLED

from pyglet.window import mouse
import math

class Camera(object):
    def __init__(self):
        self.phi = pi / 2.0
        self.theta = pi * 0.4
        self.radius = 5

        self.center = [0,0,0]
        self.up = [0,1,0]

    def location(self):
        eyeX = self.radius * cos(self.phi) * sin(self.theta) + self.center[0]
        eyeY = self.radius * cos(self.theta)                 + self.center[1]
        eyeZ = self.radius * sin(self.phi) * sin(self.theta) + self.center[2]

        return (eyeX, eyeY, eyeZ)


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    
    #if modifiers & pyglet.window.key.MOD_ALT:
    if buttons & mouse.LEFT:
        s = 0.0075
        camera.phi += s * dx
        camera.theta += s * dy
        
    if buttons & mouse.RIGHT:
        camera.radius += 0.01 * -dx
        if camera.radius < 0:
            camera.radius = 0
    
    if buttons & mouse.MIDDLE:
        s = 0.01
        camera.center[1] -= s * dy
        
        phi = camera.phi + math.pi*0.5
        camera.center[0] += cos(phi) * s * dx
        camera.center[2] += sin(phi) * s * dx


@window.event
def on_draw():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    cam_loc = camera.location()
    gluLookAt(cam_loc[0], cam_loc[1], cam_loc[2],
               camera.center[0], camera.center[1], camera.center[2],
               camera.up[0], camera.up[1], camera.up[2]);


    batch.draw()

def setup():
    # One-time GL setup
    glClearColor(0.1, 0.1, 0.1, 1)


class GridGroup(pyglet.graphics.Group):
    def set_state(self):
        glColor3f(0.2, 0.2, 0.2)
        
    def unset_state(self):
        pass

class AdditiveGroup(pyglet.graphics.Group):
    def set_state(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_COLOR, GL_DST_COLOR)
        glBlendColor(1,1,1,1)

    def unset_state(self):
        glDisable(GL_BLEND)

class AxesGroup(AdditiveGroup):
    def set_state(self):
        super(AxesGroup, self).set_state()
        
    def unset_state(self):
        super(AxesGroup, self).unset_state()
        pass

class ParticlesGroup(AdditiveGroup):
    def set_state(self):
        super(ParticlesGroup, self).set_state()
        glPointSize(3.0)
        
    def unset_state(self):
        super(ParticlesGroup, self).unset_state()
        glPointSize(1.0)

class GeometryGroup(pyglet.graphics.Group):
    def set_state(self):
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        
        # Uncomment this line for a wireframe view
        #glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        # Simple light setup.  On Windows GL_LIGHT0 is enabled by default,
        # but this is not the case on Linux or Mac, so remember to always 
        # include it.
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)

        # Define a simple function to create ctypes arrays of floats:
        def vec(*args):
            return (GLfloat * len(args))(*args)

        glLightfv(GL_LIGHT0, GL_POSITION, vec(.5, .5, 1, 0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, vec(.5, .5, .5, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, vec(1, 1, 1, 1))
        glLightfv(GL_LIGHT1, GL_POSITION, vec(1, 0, .5, 0))
        glLightfv(GL_LIGHT1, GL_DIFFUSE, vec(.5, .5, .5, 1))
        glLightfv(GL_LIGHT1, GL_SPECULAR, vec(1, 1, 1, 1))

        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, vec(0.3, 0.3, 0.3, 1))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, vec(1, 1, 1, 1))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 50)

    def unset_state(self):
        glDisable(GL_LIGHTING)
        glDisable(GL_LIGHT0)
        glDisable(GL_LIGHT1)
        


class Axes(object):
    def __init__(self, radius, batch, group=None):
        xaxis = [0.0, 0.0, 0.0, radius, 0.0, 0.0]
        yaxis = [0.0, 0.0, 0.0, 0.0, radius, 0.0]
        zaxis = [0.0, 0.0, 0.0, 0.0, 0.0, radius]
        
        colors = [  1.0,0.0,0.0, 1.0,0.0,0.0, \
                    0.0,1.0,0.0, 0.0,1.0,0.0, \
                    0.0,0.0,1.0, 0.0,0.0,1.0  ]
        
        vertices = xaxis + yaxis + zaxis
        
        self.vertex_list = batch.add(len(vertices)//3, 
                                             GL_LINES,
                                             group,
                                             ('v3f/static', vertices),
                                             ('c3f/static', colors))
       
    def delete(self):
        self.vertex_list.delete()


class Grid(object):
    def __init__(self, radius, divisions, batch, group=None):
        
        vertices = []
        idiv = 1.0 / float(divisions)
        for x in range(-divisions, divisions+1):
            xc = x*idiv*radius
            vertices += [xc, 0, -radius]
            vertices += [xc, 0, radius]
            
        
        for z in range(-divisions, divisions+1):
            zc = z*idiv*radius
            vertices += [-radius, 0, zc]
            vertices += [radius, 0, zc]
    
        self.vertex_list = batch.add(len(vertices)//3, 
                                             GL_LINES,
                                             group,
                                             ('v3f/static', vertices))
       
    def delete(self):
        self.vertex_list.delete()


class Torus(object):
    list = None
    def __init__(self, radius, inner_radius, slices, inner_slices, 
                 batch, group=None):
        # Create the vertex and normal arrays.
        vertices = []
        normals = []

        u_step = 2 * pi / (slices - 1)
        v_step = 2 * pi / (inner_slices - 1)
        u = 0.
        for i in range(slices):
            cos_u = cos(u)
            sin_u = sin(u)
            v = 0.
            for j in range(inner_slices):
                cos_v = cos(v)
                sin_v = sin(v)

                d = (radius + inner_radius * cos_v)
                x = d * cos_u
                y = d * sin_u
                z = inner_radius * sin_v

                nx = cos_u * cos_v
                ny = sin_u * cos_v
                nz = sin_v

                vertices.extend([x, y, z])
                normals.extend([nx, ny, nz])
                v += v_step
            u += u_step

        # Create a list of triangle indices.
        indices = []
        for i in range(slices - 1):
            for j in range(inner_slices - 1):
                p = i * inner_slices + j
                indices.extend([p, p + inner_slices, p + inner_slices + 1])
                indices.extend([p, p + inner_slices + 1, p + 1])

        self.vertex_list = batch.add_indexed(len(vertices)//3, 
                                             GL_TRIANGLES,
                                             group,
                                             indices,
                                             ('v3f/static', vertices),
                                             ('n3f/static', normals))
       
    def delete(self):
        self.vertex_list.delete()




class Particles(object):
    def __init__(self, num, size, batch, group=None):
        
        
        vertices = [(random.random())*size for i in range(num*3)]
        colors = [random.random() for i in range(num*3)]
        
        self.velocities = [random.random()-0.5 for i in range(num*3)]
        self.vertex_list = batch.add(len(vertices)//3, 
                                             GL_POINTS,
                                             group,
                                             ('v3f/stream', vertices),
                                             ('c3f/static', colors))
    def delete(self):
        self.vertex_list.delete()

def update(dt):
    particles.vertex_list.vertices = [v + ((random.random()-0.5) * dt) for v in particles.vertex_list.vertices]


def euler_particles(dt):
    pts = particles.vertex_list.vertices
    vel = particles.velocities
    
    for i in range(len(pts)//3):
        
        v = [vel[i*3 + 0], vel[i*3 + 1], vel[i*3 + 2]]
        p = [pts[i*3 + 0], pts[i*3 + 1], pts[i*3 + 2]]
        
        # gravity
        v[1] += -9.8*dt
        
        # ground plane collision
        if p[1] < 0:
            damp = 0.3
            v[0] = v[0]*damp
            v[1] = -v[1]*damp
            v[2] = v[2]*damp
        
        # euler
        p[0] = p[0] + v[0]*dt
        p[1] = p[1] + v[1]*dt
        p[2] = p[2] + v[2]*dt
        
        # copy back
        vel[i*3 + 0] = v[0]
        vel[i*3 + 1] = v[1]
        vel[i*3 + 2] = v[2]

        pts[i*3 + 0] = p[0]
        pts[i*3 + 1] = p[1]
        pts[i*3 + 2] = p[2]

        
        

#pyglet.clock.schedule(update)
pyglet.clock.schedule(euler_particles)

geogroup = GeometryGroup()
gridgroup = GridGroup()
axesgroup = AxesGroup()
partgroup = ParticlesGroup()
batch = pyglet.graphics.Batch()

camera = Camera()

setup()

grid = Grid(2, 6, batch, group=gridgroup )
axes = Axes(0.5, batch, group=axesgroup )
#torus = Torus(1, 0.3, 20, 10, group=geogroup, batch=batch)
particles = Particles(1000, 3, batch, group=partgroup)
pyglet.app.run()
