
from random import random

import euclid
from euclid import Vector3, Point3
import math

import ui2d
import ui3d

import pyglet
from pyglet.gl import *
from pyglet.window import mouse

import camera

import numpy as np

try:
    # Try and create a window with multisampling (antialiasing)
    config = Config(sample_buffers=1, samples=4, depth_size=16, double_buffer=True,)
    window = pyglet.window.Window(1280, 720, resizable=True, config=config)
except pyglet.window.NoSuchConfigException:
    # Fall back to no multisampling for old hardware
    window = pyglet.window.Window(resizable=True)



@window.event
def on_mouse_press(x, y, buttons, modifiers):
    return
    if buttons & mouse.LEFT:
        click, dir = camera.project_ray(x, y)
        #cross = Ray(click, dir, 20)
        particles.intersect(click, dir)


# @window.event
def on_draw():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    (width, height)= window.get_size()
    camera.view_update(width, height)
    
    glLoadIdentity()

    gluLookAt(camera.loc[0], camera.loc[1], camera.loc[2],
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
        


class Particles(object):
    
    def intersect(self, pt, dir):
        for i, loc in enumerate(self.locs):
            p = Point3(loc[0], loc[1], loc[2])
            v = (p - camera.loc).normalize()
            
            if v.dot(dir) > 0.999:
                self.vels[i][0] += 3*(random()-0.5)
                self.vels[i][1] += 4 + 3*random()
                self.vels[i][2] += 3*(random()-0.5)
                
        self.flush()
    
    def flush(self):
        a = tuple(self.locs.flat)
        
        if hasattr(self, "vertex_list"):
            self.vertex_list.vertices = a
        else:
            self.vertices = a
    
    def __init__(self, num, size, batch, group=None):
        self.num = num
        self.size = size


        self.locs = (np.random.rand(num, 3)-0.5)*size
        self.locs += np.array([0,size,0])
        self.vels = (np.random.rand(num, 3)-0.5)
        self.flush()
        
        #colors = [random() for i in range(num*3)]
        colors = [0.5]*(num*3)
        self.vertex_list = batch.add(len(self.vertices)//3, 
                                             GL_POINTS,
                                             group,
                                             ('v3f/stream', self.vertices),
                                             ('c3f/static', colors))
    def delete(self):
        self.vertex_list.delete()

def euler_particles(dt):
    vels = particles.vels
    locs = particles.locs
    
    # gravity
    vels += np.array([0, -9.8*dt, 0])
    
    # ground plane collision
    damp = 0.4
    y_lt_zero = locs[:,1] < 0

    vels[y_lt_zero] *= np.array([damp,-damp,damp])
    locs[y_lt_zero] *= np.array([1,0,1])

    # euler 
    locs += vels*dt
    
    particles.flush()


pyglet.clock.schedule(euler_particles)

geogroup = GeometryGroup()
gridgroup = GridGroup()
axesgroup = AxesGroup()
partgroup = ParticlesGroup()
batch = pyglet.graphics.Batch()

camera = camera.Camera(window)

setup()


ui = ui2d.Ui(window)
#ui.addControl()

# use this rather than decorator, 
# so that ui drawing is higher in the stack
window.push_handlers(on_draw)




grid = ui3d.Grid(2, 6, batch, group=gridgroup )
axes = ui3d.Axes(0.5, batch, group=axesgroup )
particles = Particles(50000, 3, batch, group=partgroup)

pyglet.app.run()
'''

import cProfile
cProfile.run('pyglet.app.run()', '/tmp/pyprof')
import pstats
stats = pstats.Stats('/tmp/pyprof')
stats.sort_stats('time')
stats.print_stats()
'''