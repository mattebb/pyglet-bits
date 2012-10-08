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
from pyglet import graphics
from pyglet.gl import *
from shader import Shader

from ui3d import Grid, Axes
from parameter import Parameter, Color3

glsl_util = ''.join(open('util.glsl').readlines())



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
        self.ui3d_batch = pyglet.graphics.Batch()

        self.grid = Grid(2, 6, self.ui3d_batch )
        self.axes = Axes(0.5, self.ui3d_batch )
        
    def on_draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # 3D Geometry
        for ob in self.objects:
            ob.draw(time=self.time, camera=self.camera)

        # 3D UI elements
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glHint (GL_LINE_SMOOTH_HINT, GL_NICEST);
        
        self.ui3d_shader.bind()
        self.ui3d_shader.uniform_matrixf('modelview', self.camera.matrix)
        self.ui3d_shader.uniform_matrixf('projection', self.camera.persp_matrix)
        self.ui3d_batch.draw()
        self.ui3d_shader.unbind()

        glDisable(GL_LINE_SMOOTH)

    
    def update(self, dt):
        if self.playback == self.PLAYING:
            self.time += dt
        
        for ob in self.objects:
            ob.update(self.time, dt=dt)




class Object3d(object):
    vertex_shader = '''
    uniform mat4 modelview;
    uniform mat4 projection;
    varying vec3 normal;
    void main() {
        gl_FrontColor = gl_Color;
        
        vec4 modelSpacePos = modelview * gl_Vertex;
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

    def transform_verts(self, verts, matrix):
        ''' Transform a numpy array of vertex positions by a matrix '''
        # rotate 90 degrees to Y up, from blender
        mat = np.matrix( matrix[:] ).reshape(4,4)
        # change verts to vec4
        verts = np.insert(verts, 3, 1.0, axis=1)
        # multiply and transpose back to array of vec3
        verts = np.dot(mat.T, verts.T)[:-1].T
        return verts

    def calculate_normals(self, verts, idx):
        v1 = verts[idx[::3]]
        v1_indices = idx[:,0]
        v2_indices = idx[:,1]
        v3_indices = idx[:,2]

        # take first 2 edges of each tri
        edge1 = verts[v1_indices] - verts[v2_indices]
        edge2 = verts[v1_indices] - verts[v3_indices]

        # generate normal for each face
        fnrm = np.cross(edge1, edge2)
        # normalise
        fnrm /= ( np.sqrt( fnrm[:,0]**2 + fnrm[:,1]**2 + fnrm[:,2]**2 ).reshape(-1,1) )

        # crazy generator exp to make smooth normals by
        # summing normals of faces adjacent to each vertex
        #print([np.sum(fnrm[j] for j, fi in enumerate(idx) if i in fi) for i in range(len(verts))])
        vn = np.vstack([ np.sum(fnrm[j] for j, fi in enumerate(idx) if i in fi) for i in range(len(verts)) ])

        #print(vn)
        # normalise vertex normals
        vn /= ( np.sqrt( vn[:,0]**2 + vn[:,1]**2 + vn[:,2]**2 ).reshape(-1,1) )

        return vn

    def __init__(self, scene):
        self.batch = pyglet.graphics.Batch()
        
        self.translate = Vector3(0,0,0)
        self.rotate= Vector3(0,0,0)
        self.scale= Vector3(1,1,1)
        
        self.shader = Shader(self.vertex_shader, self.fragment_shader)

        scene.objects.append( self )
    
    def update(self, time, dt=0):
        pass
    
    def draw(self, **kwargs):
        pass

# XXX
def myfunc():
    monkey = Raw(scene)
    monkey.translate = testp.getval()[:]
    ui.layout.addParameter(ui, monkey.color)
    #return 
    #return ui3d.Grid(2, 6, batch)

# rawob = Raw(scene)
# ui.layout.addParameter(ui, rawob.color)

# cube = Cube( scene )
# p = Parameter(object=cube, attr="translate")
# ui.layout.addParameter(ui, p)


class Raw(Object3d):
    vertex_shader = '''
    uniform float time;
    uniform mat4 modelview;
    uniform mat4 projection;
    varying vec3 normal;
    void main() {
        gl_FrontColor = gl_Color;
        
        vec3 P = gl_Vertex.xyz; 
        vec3 N = gl_Normal.xyz;
        
        // transform the vertex position
        vec3 v = P + N*0.2*(0.5+0.5*sin(time*1.5));
        vec4 modelSpacePos = modelview * vec4(v, 1.0);
        gl_Position = projection * modelSpacePos;
        
        normal = normalize(modelview * vec4(N, 0.0)).xyz;

    }
    '''
    fragment_shader = glsl_util+'''
    varying vec3 normal;
    uniform vec3 color;
    void main(void) {
        vec3 L = normalize( vec3( gl_LightSource[1].position ) );
        vec4 col = gl_Color * vec4(color,1.0) * dot(L, normal);
        gl_FragColor = linearrgb_to_srgb( col );
        
    }
    
    '''
    
    def __init__(self, *args, **kwargs):
        super(Raw, self).__init__(*args, **kwargs)

        import import_raw
        self.vertices, self.indices = import_raw.readMeshRAW('trim.raw')
        
        verts = np.array(self.vertices).reshape(-1,3)
        idx = np.array(self.indices).reshape(-1,3)

        verts = self.transform_verts(verts, Matrix4.new_rotate_axis(math.pi*-0.5, Vector3(1,0,0)) )
        vn = self.calculate_normals(verts, idx)
        
        self.vertices = tuple(verts.flat)
        self.normals = tuple(vn.flat)
        self.indices = tuple(idx.flat)
        self.vertex_list = self.batch.add_indexed(len(self.vertices)//3,
                                             GL_TRIANGLES,
                                             None,
                                             self.indices,
                                             ('v3f/static', self.vertices),
                                             ('n3f/static', self.normals)
                                             )
        self.color = Parameter(default=Color3(0.9, 0.3, 0.4), vmin=0.0, vmax=1.0)

    def draw(self, time=0, camera=None):
        # stupid rotate_euler taking coords out of order!
        m = Matrix4.new_translate(*self.translate).rotate_euler(*self.rotate.yzx).scale(*self.scale)

        self.shader.bind()
        self.shader.uniformf('time', time)
        self.shader.uniformf('color', *self.color.getval())
        self.shader.uniform_matrixf('modelview', camera.matrix * m)
        self.shader.uniform_matrixf('projection', camera.persp_matrix)
        
        self.batch.draw()
        self.shader.unbind()

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
    fragment_shader = glsl_util + '''
    varying vec3 normal;
    void main(void) {
        vec3 L = normalize( vec3( gl_LightSource[1].position ) );
        gl_FragColor = linearrgb_to_srgb( gl_Color * dot(L, normal) );
        
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

