import pyglet

# Disable error checking for increased performance
pyglet.options['debug_gl'] = False

from random import random

import euclid
from euclid import Vector3, Point3, Matrix4
import math

import ui2d
import ui3d

import ctypes




from pyglet.gl import *
from pyglet.window import mouse
from shader import Shader

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
window = pyglet.window.Window(600, 300, resizable=True)
#window.set_location(2600, 800)
window.set_location(1200, 800)

@window.event
def on_mouse_press(x, y, buttons, modifiers):
    return
    if buttons & mouse.LEFT:
        click, dir = camera.project_ray(x, y)
        #cross = Ray(click, dir, 20)
        particles.intersect(click, dir)
    
def setup():
    # One-time GL setup
    glClearColor(0.4, 0.4, 0.4, 1)
    
    

class AdditiveGroup(pyglet.graphics.Group):
    def set_state(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_COLOR, GL_DST_COLOR)
        glBlendColor(1,1,1,1)

    def unset_state(self):
        glDisable(GL_BLEND)

class ParticlesGroup(AdditiveGroup):
    def set_state(self):
        super(ParticlesGroup, self).set_state()
        glPointSize(3.0)
        
    def unset_state(self):
        super(ParticlesGroup, self).unset_state()
        glPointSize(1.0)
        
class Scene(object):
    
    PAUSED = 0
    PLAYING = 1
    
    vertex_shader = '''
    uniform mat4 modelview;
    uniform mat4 projection;
    void main() {
        gl_FrontColor = gl_Color;
        
        vec4 modelSpacePos = modelview * gl_Vertex;
        gl_Position = projection * modelSpacePos;
    }
    '''

    def __init__(self):
        self.objects = []
        self.camera = None
        
        self.playback = self.PLAYING
        self.time = 0   # in seconds?
        
        self.ui3d_shader = Shader(self.vertex_shader)
        
    def on_draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # 3D Geometry
        for ob in scene.objects:
            ob.draw(time=self.time, camera=camera)

        # 3D UI elements
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glHint (GL_LINE_SMOOTH_HINT, GL_NICEST);
        
        self.ui3d_shader.bind()
        self.ui3d_shader.uniform_matrixf('modelview', self.camera.matrix)
        self.ui3d_shader.uniform_matrixf('projection', self.camera.persp_matrix)
        batch.draw()
        self.ui3d_shader.unbind()

        glDisable(GL_LINE_SMOOTH)

    
    def update(self, dt):
        if self.playback == self.PLAYING:
            self.time += dt
        
        for ob in self.objects:
            ob.update(self.time, dt=dt)

class Object3d(object):
    def __init__(self, scene):
        self.batch = pyglet.graphics.Batch()
        
        self.translate = Vector3(0,0,0)
        self.rotate= Vector3(0,0,0)
        self.scale= Vector3(1,1,1)
        
        scene.objects.append( self )
    
    def update(self, time, dt=0):
        pass
    
    def draw(self, **kwargs):
        pass
        
class Anim(object):
    def __init__(self, prev_val):
        self.prev_val = prev_val
    
    def setval(self, time):
        pass

class Cube(Object3d):
    
    vertex_shader = '''
        uniform float time;
        uniform mat4 modelview;
        uniform mat4 projection;
        varying vec3 normal;
        void main() {
            gl_FrontColor = gl_Color;
            
            vec3 P = gl_Vertex.xyz; 
            // transform the vertex position
            vec4 v = (vec4(P,1.0) + vec4(0,1,0,0)*sin(time*2.0*gl_Vertex.z));
            vec4 modelSpacePos = modelview * v;
            gl_Position = projection * modelSpacePos;
            
            vec3 N = gl_Normal.xyz; 
            normal = normalize(modelview * vec4(N, 0.0)).xyz;

        }
        '''
    fragment_shader = '''
        varying vec3 normal;
        void main(void) {
            vec3 L = normalize( vec3( gl_LightSource[1].position ) );
            gl_FragColor = gl_Color * dot(L, normal);
            
        }
        
        '''

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
 
        idx = np.array(self.indices).reshape(-1,3)
        verts = np.array(self.vertices).reshape(-1,3)
    
        v1 = verts[::4] - verts[1::4]
        v2 = verts[::4] - verts[3::4]
        
        nrm = np.repeat(np.cross(v1, v2), 4, axis=0)
        
        # normalise
        nrm /= ( np.sqrt( nrm[:,0]**2 + nrm[:,1]**2 + nrm[:,2]**2 ).reshape(-1,1) )
        
        self.normals = nrm.flat
        
        self.vertex_list = self.batch.add_indexed(len(self.vertices)//3,
                                             GL_TRIANGLES,
                                             None,
                                             self.indices,
                                             ('v3f/static', self.vertices),
                                             ('n3f/static', self.normals),
                                             )
        self.shader = Shader(self.vertex_shader, self.fragment_shader)
    
    def draw(self, time=0, camera=None):
        # stupid rotate_euler taking coords out of order!
        m = Matrix4.new_translate(*self.translate).rotate_euler(*self.rotate.yzx).scale(*self.scale)

        self.shader.bind()
        self.shader.uniformf('time', time)
        self.shader.uniform_matrixf('modelview', camera.matrix * m)
        self.shader.uniform_matrixf('projection', camera.persp_matrix)
        
        self.batch.draw()
        self.shader.unbind()
        
        
    def update(self, time, dt=0):
        return
        
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
pyglet.clock.schedule(scene.update)


partgroup = ParticlesGroup()
batch = pyglet.graphics.Batch()


camera = camera.Camera(window)
scene.camera = camera

setup()

def myfunc():
    return ui3d.Grid(2, 6, batch)

grid = ui3d.Grid(2, 6, batch )
axes = ui3d.Axes(0.5, batch )
particles = Particles(2, 3, batch, group=partgroup)


for i in range(30):
    s = 7
    cube = Cube( scene )
    cube.translate = Point3((random()-0.5)*s, (random()-0.5)*s, (random()-0.5)*s)
    cube.rotate = Vector3(random(), random(), random())
    cube.scale = Vector3(random()*0.3, random()*0.3, random()*0.3)


ui = ui2d.Ui(window)
ui.layout.addControl(ui, object=particles, attr="force")
ui.layout.addControl(ui, object=camera, attr="fov")
#ui.layout.addControl(ui, object=cube, attr="translate", vmin=-10, vmax=10)
#ui.layout.addControl(ui, object=cube, attr="rotate", vmin=-6, vmax=6, subtype=ui2d.UiControls.ANGLE)
#ui.layout.addControl(ui, object=cube, attr="scale", vmin=-10, vmax=10)
ui.layout.addControl(ui, func=myfunc)

#ui.addControl(ui2d.UiControls.SLIDER, object=camera, attr="fov", vmin=5, vmax=120)
#ui.addControl(ui2d.UiControls.SLIDER, object=cube, attr="translate", vmin=-10, vmax=10)
#ui.addControl(func=myfunc)


# use this rather than decorator, 
# so that ui drawing is higher in the stack
#window.push_handlers(on_draw)
window.push_handlers(scene)





pyglet.app.run()
'''

import cProfile
cProfile.run('pyglet.app.run()', '/tmp/pyprof')
import pstats
stats = pstats.Stats('/tmp/pyprof')
stats.strip_dirs().sort_stats('time')
stats.print_stats(25)

print 'INCOMING CALLERS:'
stats.print_callers(25)

print 'OUTGOING CALLEES:'
stats.print_callees(25)
'''
