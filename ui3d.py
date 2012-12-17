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
    def __init__(self, radius, divisions, batch, center=(0,0,0), group=None):
        
        vertices = []
        idiv = 1.0 / float(divisions)
        cx = center[0]
        cy = center[1]
        cz = center[2]

        for x in range(-divisions, divisions+1):
            xc = x*idiv*radius
            vertices += [xc+cx, cy, -radius+cz]
            vertices += [xc+cx, cy, radius+cz]
            
        
        for z in range(-divisions, divisions+1):
            zc = z*idiv*radius
            vertices += [-radius+cx, cy, zc+cz]
            vertices += [radius+cx, cy, zc+cz]
    
        colors = [0.28,0.28,0.28,1.0]*(len(vertices)//3)


        #from ui2ddraw import aajitter
        #vertices, colors = aajitter(vertices, colors, sc=0.005)

        self.vertex_list = batch.add(len(vertices)//3, 
                                             GL_LINES,
                                             group,
                                             ('v3f/static', vertices),
                                             ('c4f/static', colors))
       
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