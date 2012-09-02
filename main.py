from random import random

import euclid
from euclid import Vector3, Point3, Matrix4
import math

import ui2d
import ui3d

import ctypes

import pyglet
from pyglet.gl import *
from pyglet.window import mouse

import camera

import numpy as np
'''
try:
    # Try and create a window with multisampling (antialiasing)
    config = Config(sample_buffers=1, samples=4, depth_size=16, double_buffer=True,)
    window = pyglet.window.Window(720, 360, resizable=True, config=config)
except pyglet.window.NoSuchConfigException:
    # Fall back to no multisampling for old hardware
    window = pyglet.window.Window(resizable=True)
'''
window = pyglet.window.Window(500, 300, resizable=True)
#window.set_location(2600, 800)
window.set_location(1600, 800)

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
    
    for ob in scene.objects:
        ob.draw()
    
def setup():
    # One-time GL setup
    glClearColor(0.4, 0.4, 0.4, 1)


class GridGroup(pyglet.graphics.OrderedGroup):
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
        
class Scene(object):
    def __init__(self):
        self.objects = []

class Object3d(object):
    def __init__(self, scene):
        self.batch = pyglet.graphics.Batch()
        self.group = pyglet.graphics.Group()
        
        #self.matrix = Matrix4()
        self.translate = Vector3(0,0,0)
        self.rotate= Vector3(0,0,0)
        self.scale= Vector3(1,1,1)
        
        scene.objects.append( self )

class Cube(Object3d):
    
    def __init__(self, *args, **kwargs):
        super(Cube, self).__init__(*args, **kwargs)
        
        self.vertices = [
                      # Front face
                      -1.0, -1.0,  1.0,
                       1.0, -1.0,  1.0,
                       1.0,  1.0,  1.0,
                      -1.0,  1.0,  1.0,
                       
                      # Back face
                      -1.0, -1.0, -1.0,
                      -1.0,  1.0, -1.0,
                       1.0,  1.0, -1.0,
                       1.0, -1.0, -1.0,
                       
                      # Top face
                      -1.0,  1.0, -1.0,
                      -1.0,  1.0,  1.0,
                       1.0,  1.0,  1.0,
                       1.0,  1.0, -1.0,
                       
                      # Bottom face
                      -1.0, -1.0, -1.0,
                       1.0, -1.0, -1.0,
                       1.0, -1.0,  1.0,
                      -1.0, -1.0,  1.0,
                       
                      # Right face
                       1.0, -1.0, -1.0,
                       1.0,  1.0, -1.0,
                       1.0,  1.0,  1.0,
                       1.0, -1.0,  1.0,
                       
                      # Left face
                      -1.0, -1.0, -1.0,
                      -1.0, -1.0,  1.0,
                      -1.0,  1.0,  1.0,
                      -1.0,  1.0, -1.0
                    ]

        self.indices = [
                      0,  1,  2,      0,  2,  3,    # front
                      4,  5,  6,      4,  6,  7,    # back
                      8,  9,  10,     8,  10, 11,   # top
                      12, 13, 14,     12, 14, 15,   # bottom
                      16, 17, 18,     16, 18, 19,   # right
                      20, 21, 22,     20, 22, 23    # left
                    ]
 
        self.vertex_list = self.batch.add_indexed(len(self.vertices)//3,
                                             GL_TRIANGLES,
                                             self.group,
                                             self.indices,
                                             ('v3f/static', self.vertices),
                                             )
    
    def draw(self):
        m = Matrix4.new_translate(*self.translate).rotate_euler(*self.rotate).scale(*self.scale)
        
        glPushMatrix()
        glMultMatrixf( (ctypes.c_float*16)(*m) )
        self.batch.draw()
        glPopMatrix()
        
    
    def delete(self):
        self.vertex_list.delete()

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

        self.force = False

        self.locs = (np.random.rand(num, 3)-0.5)*size
        self.locs += np.array([0,size,0])
        self.vels = (np.random.rand(num, 3)-0.5)
        self.flush()

        #colors = [0.5]*(num*3)
        colors = tuple(np.random.rand(num, 3).flat)
        
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

    # force test
    if particles.force == True:
        vels += np.array([5*dt, 0, 0])

    # euler 
    locs += vels*dt
    
    particles.flush()


pyglet.clock.schedule(euler_particles)

scene = Scene()

geogroup = GeometryGroup()
gridgroup = GridGroup(0)
axesgroup = AxesGroup()
partgroup = ParticlesGroup()
batch = pyglet.graphics.Batch()

camera = camera.Camera(window)

setup()

def myfunc():
    return ui3d.Grid(2, 6, batch, group=gridgroup )

#grid = ui3d.Grid(2, 6, batch, group=gridgroup )
axes = ui3d.Axes(0.5, batch, group=axesgroup )
particles = Particles(2, 3, batch, group=partgroup)
cube = Cube( scene )

ui = ui2d.Ui(window)
ui.layout.addControl(ui, object=particles, attr="force")
ui.layout.addControl(ui, object=camera, attr="fov")
ui.layout.addControl(ui, object=cube, attr="translate", vmin=-10, vmax=10)
ui.layout.addControl(ui, func=myfunc)

#ui.addControl(ui2d.UiControls.SLIDER, object=camera, attr="fov", vmin=5, vmax=120)
#ui.addControl(ui2d.UiControls.SLIDER, object=cube, attr="translate", vmin=-10, vmax=10)
#ui.addControl(func=myfunc)


# use this rather than decorator, 
# so that ui drawing is higher in the stack
window.push_handlers(on_draw)






pyglet.app.run()
'''

import cProfile
cProfile.run('pyglet.app.run()', '/tmp/pyprof')
import pstats
stats = pstats.Stats('/tmp/pyprof')
stats.sort_stats('time')
stats.print_stats()
'''
