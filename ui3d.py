import pyglet
from pyglet.gl import *

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