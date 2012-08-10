
from math import pi, sin, cos
from random import random

import euclid
from euclid import Vector3, Point3

import pyglet
from pyglet.gl import *

from pyglet.window import key

try:
    # Try and create a window with multisampling (antialiasing)
    config = Config(sample_buffers=1, samples=4, depth_size=16, double_buffer=True,)
    window = pyglet.window.Window(resizable=True, config=config)
except pyglet.window.NoSuchConfigException:
    # Fall back to no multisampling for old hardware
    window = pyglet.window.Window(resizable=True)

keys = key.KeyStateHandler()
window.push_handlers(keys)

@window.event
def on_resize(width, height):
    camera.view_update(width, height)
    return pyglet.event.EVENT_HANDLED

from pyglet.window import mouse
import math
class Camera(object):

    def __init__(self):
        self.phi = pi / 2.0
        self.theta = pi * 0.4
        self.radius = 5.
        self.fov = 50.
        self.clipnear = 0.1
        self.clipfar = 1000
        
        self.center = Vector3(0,0,0)
        self.up = Vector3(0,1,0)

        self.needs_update = False

    def location(self):
        eyeX = self.radius * cos(self.phi) * sin(self.theta) + self.center[0]
        eyeY = self.radius * cos(self.theta)                 + self.center[1]
        eyeZ = self.radius * sin(self.phi) * sin(self.theta) + self.center[2]
        return Vector3(eyeX, eyeY, eyeZ)
        
    def project_ray(self, px, py):
        loc = self.location()
        cam_view = (self.center - loc).normalize()
        
        self.cam_h =  cam_view.cross(self.up).normalize()
        self.cam_v = -1 * cam_view.cross(self.cam_h).normalize()
        
        half_v = math.tan(math.radians(self.fov)*0.5) * self.clipnear
        win = window.get_size()
        aspect = win[0] / float(win[1])
        half_h = half_v * aspect
        
        # mouse to ndc
        nx = (px - win[0]*0.5) / (win[0]*0.5)
        ny = (py - win[1]*0.5) / (win[1]*0.5)
        
        self.cam_h *= half_h
        self.cam_v *= half_v

        click = loc + (cam_view*self.clipnear)  + (nx * self.cam_h) + (ny * self.cam_v)

        '''
        modelview = (GLdouble * 16)()
        projection = (GLdouble * 16)()
        view = (GLint * 4)()
        
        glGetDoublev (GL_MODELVIEW_MATRIX, modelview);
        glGetDoublev (GL_PROJECTION_MATRIX, projection);
        glGetIntegerv( GL_VIEWPORT, view );
        
        wx,wy,wz = GLdouble(),GLdouble(),GLdouble() 
        gluUnProject(px, py, self.clipnear, modelview, projection, view, wx, wy, wz)
        click = Vector3(wx.value, wy.value, wz.value)
        '''
        dir = (click - loc).normalize()
        return click, dir
    
    def view_update(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, width / float(height), self.clipnear, self.clipfar)
        glMatrixMode(GL_MODELVIEW)


@window.event
def on_mouse_press(x, y, buttons, modifiers):
    if buttons & mouse.LEFT:
        click, dir = camera.project_ray(x, y)
        #cross = Ray(click, dir, 20)
        particles.intersect(click, dir)

@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    
    import platform
    if platform.system() != 'Darwin':
        dy = -dy

    if modifiers & pyglet.window.key.MOD_SHIFT:
        if buttons & mouse.RIGHT:
            camera.fov -= dx
            if camera.fov < 5.:
                camera.fov = 5.
            elif camera.fov > 150:
                camera.fov = 150
        
            winsize = window.get_size()
            camera.view_update(winsize[0], winsize[1])

    elif keys[key.SPACE]:
        if buttons & mouse.LEFT:
            s = 0.0075
            camera.phi += s * dx
            camera.theta -= s * dy
            if camera.theta > pi:
                camera.theta = pi
            elif camera.theta < 0.0001:
                camera.theta = 0.0001
            
        if buttons & mouse.RIGHT:
            camera.radius += 0.01 * -dx
            if camera.radius < 0:
                camera.radius = 0
        
        if buttons & mouse.MIDDLE:
            s = 0.01
            camera.center[1] += s * dy
            
            phi = camera.phi + math.pi*0.5
            camera.center[0] += cos(phi) * s * dx
            camera.center[2] += sin(phi) * s * dx
    
   


@window.event
def on_draw():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    if camera.needs_update:
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


class Cross(object):
    def __init__(self, pt, size, group=None):
        vertices = [pt[0]-size, pt[1], pt[2], pt[0]+size, pt[1], pt[2], \
                    pt[0], pt[1], pt[2]-size, pt[0], pt[1], pt[2]+size ]
        colors = [0.0,1.0,1.0]*2 + [1,0,0]*2
        self.vertex_list = batch.add(len(vertices)//3, 
                                             GL_LINES,
                                             group,
                                             ('v3f/static', vertices),
                                             ('c3f/static', colors))

    def delete(self):
        self.vertex_list.delete()

class Ray(object):
    def __init__(self, pt, dir, length, group=None):
        pt2 = pt + (dir*length)
        vertices = pt[:] + pt2[:]
        colors = [1.0,0.0,1.0]*2
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

'''
@window.event
def on_key_release(symbol, modifiers):
    if symbol & pyglet.window.key.SPACE:
        particles.locs = particles.random_locations()
        particles.flush()
        #particles.
    #    particles.vertex_list.vertices = 
'''

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
particles = Particles(1000, 3, batch, group=partgroup)
pyglet.app.run()
