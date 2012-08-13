

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

try:
    # Try and create a window with multisampling (antialiasing)
    config = Config(sample_buffers=1, samples=4, depth_size=16, double_buffer=True,)
    window = pyglet.window.Window(resizable=True, config=config)
except pyglet.window.NoSuchConfigException:
    # Fall back to no multisampling for old hardware
    window = pyglet.window.Window(resizable=True)



@window.event
def on_mouse_press(x, y, buttons, modifiers):
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
        


class Particles(object):
    
    def intersect(self, pt, dir):
        for i, loc in enumerate(self.locs):
            p = Point3(loc[0], loc[1], loc[2])
            v = (p - camera.location()).normalize()
            if v.dot(dir) > 0.999:
                self.vels[i][0] += 3*(random()-0.5)
                self.vels[i][1] += 4 + 3*random()
                self.vels[i][2] += 3*(random()-0.5)
                
        self.flush()
    
    def random_locations(self):
        def rloc():
            return (random()-0.5)*self.size
        return [ [rloc(), rloc()+self.size, rloc()]  for i in range(self.num) ]
    
    def flush(self):
        if hasattr(self, "vertex_list"):
            self.vertex_list.vertices = [item for sublist in self.locs for item in sublist]
        else:
            self.vertices = [item for sublist in self.locs for item in sublist]
    
    def __init__(self, num, size, batch, group=None):
        
        
        self.num = num
        self.size = size
        
        def rvel():
            return (random()-0.5)*size

        self.locs = self.random_locations()
        self.vels = [ [rvel(), rvel(), rvel()] for i in range(num) ]
        self.flush()
        
        colors = [random() for i in range(num*3)]
        self.vertex_list = batch.add(len(self.vertices)//3, 
                                             GL_POINTS,
                                             group,
                                             ('v3f/stream', self.vertices),
                                             ('c3f/static', colors))
    def delete(self):
        self.vertex_list.delete()

def euler_particles(dt):

    for i, p in enumerate(particles.locs):
        v = particles.vels[i]
        
        # gravity
        if p[1] > 0.001:
            v[1] += -9.8*dt
        
        # ground plane collision
        if p[1] < 0:
            damp = 0.4
            v[0] = v[0]*damp
            v[1] = -v[1]*damp
            v[2] = v[2]*damp
            
            p[1] = 0

        # euler 
        p[0] = p[0] + v[0]*dt
        p[1] = p[1] + v[1]*dt
        p[2] = p[2] + v[2]*dt
    
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
ui.addControl()

# use this rather than decorator, 
# so that ui drawing is higher in the stack
window.push_handlers(on_draw)

grid = ui3d.Grid(2, 6, batch, group=gridgroup )
axes = ui3d.Axes(0.5, batch, group=axesgroup )
particles = Particles(10, 3, batch, group=partgroup)
pyglet.app.run()
