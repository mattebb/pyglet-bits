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

from pyglet.gl import *

import math
from math import sin, cos, pi
from random import random

import numpy as np

np.set_printoptions(precision=3,suppress=True)



# copied from cgkit
# planeHammersley
def planeHammersley(n):
    """Yields n Hammersley points on the unit square in the xy plane.

    This function yields a sequence of n tuples (x,y) which
    represent a point on the unit square. The sequence of points for
    a particular n is always the same.  When n changes an entirely new
    sequence will be generated.
    
    This function uses a base of 2.
    """
    for k in range(n):
        u = 0
        p=0.5
        kk = k
        while kk>0:
            if kk & 1:
                u += p
            p *= 0.5
            kk >>= 1
        v = (k+0.5)/n
        yield (u, v)

aasamples = 6
hammersley_pts = np.array(list(planeHammersley(aasamples)))

def aajitter(seq, colors, sc=1.0):
    ar = np.array(seq).reshape(-1,2)
    jitter_ar = np.tile(ar, (aasamples,1))
    jitter_ar += np.repeat(hammersley_pts, len(ar), axis=0)

    colors = np.array(colors).reshape(-1,4)
    colors *= np.array( [1,1,1, 1.0/aasamples] )
    colors = np.tile(colors, (aasamples,1))

    return ( list(jitter_ar.flat), list(colors.flat) )

def strip_fix(sequence, size):
    '''
    add degenerate verts at start and end to satisfy pyglet QUAD_STRIP handling
    '''
    l = list(sequence)
    return l[:size] + l + l[-size:]


def fit(v, mi, mx):
    return (v  * (mx-mi)) + mi

def round_strip(x, y, w, h, r, corners='0123'):
    geo = []
    rsteps = 2      # radial divisions
    ch = h - 2*r    # central area height
    
    # draw rounded box, horizontal quads, bottom to top
    for i in range(-rsteps,rsteps+1):
        theta = pi/2.0 * i/(float(rsteps))
        
        if i == 0:
            # central rect
            geo += [x, r+y,      x+w, r+y]
            geo += [x, r+y+ch,   x+w, r+y+ch]
        else:
            # rounded edges
            ct = cos(theta)

            if i > 0:
                x2 = ct*r if '1' in corners else r
                x1 = r*(1-ct) if '0' in corners else 0
                
                y0 = sin(theta)*r + r                
                y0 += ch
            else:
                x2 = ct*r if '2' in corners else r
                x1 = r*(1-ct) if '3' in corners else 0
                y0 = sin(theta)*r + r

            geo += [x1+x, y0+y,  x2+x+w-r, y0+y]
    return geo
    
def roundbase(x, y, w, h, r, col1, col2, index=0, corners='0123'):
    geo = round_strip(x,y,w,h,r,corners)
    geo = strip_fix(geo, 2)
    
    # generate uv v coord from vertex y height
    v = np.array(geo).reshape(-1,2)[:,1]
    
    # convert to color values, scaled 0 to 1
    colors = np.repeat(v, 4).reshape(-1,4)
    colors = (colors - np.min(colors)) / (np.max(colors) - np.min(colors))

    # map target gradient colours to 0,1
    colors = fit(colors, np.array(col1), np.array(col2))
    colors = list(colors.flat)

    return {'id': 'roundbase%d' % index,
            'len': len(geo)//2,
            'mode':GL_QUAD_STRIP,
            'vertices':geo,
            'colors':colors
            }
    

def roundoutline(x, y, w, h, r, col, index=0, corners='0123'):
    geo = round_strip(x, y, w, h, r, corners=corners)
    garray = np.array( geo ).reshape(-1,2)

    # re-arrange quad strip vertex list into a loop
    leftside = garray[::2]             # even vertices
    rightside = garray[1::2][::-1]     # odd vertices, reversed
    outline = np.append(leftside, rightside).reshape(-1,2)
    
    # double up & roll verts for GL_LINES
    outline = np.repeat(outline, 2, axis=0)
    outline = np.roll(outline, -1, axis=0)
    outline = list( outline.flat )

    colors = col*(len(outline)//2)
    
    outline, colors = aajitter(outline, colors)

    return {'id': 'roundoutline%d' % index,
            'len': len(outline)//2,
            'mode':GL_LINES,
            'vertices':outline,
            'colors':colors
            }

def checkmark(x, y, w, h, col):

    checkmark =   [ x+w*0.2, y+h*0.5,
                    x+w*0.5, y+h*0.2,
                    x+w*0.5, y+h*0.2,
                    x+w*1.3, y+h+0.3*h ]

    colors = col*(len(checkmark)//2)
    
    checkmark, colors = aajitter(checkmark, colors)

    return {'id':'checkmarkoutline',
            'len': len(checkmark)//2,
            'mode': GL_LINES,
            'vertices': checkmark,
            'colors': colors
            }

def generate_coords(geo, x, y, w, h):
    uvs = np.array(geo).reshape(-1,2)
    minx = np.min(uvs[:,0])
    miny = np.min(uvs[:,1])
    width = np.max(uvs[:,0]) - minx
    height = np.max(uvs[:,1]) - miny
    uvs[:,1] = (uvs[:,1] - miny) / float(height)
    uvs[:,0] = (uvs[:,0] - minx) / float(width)
    return list(uvs.flat)
    
def colorwheel(x, y, w, h, v):
    steps = 48
    dtheta = (pi*2) / float(steps)

    cx = x + int(w*0.5)
    cy = y + int(h*0.5)

    # center circle
    wheel = [cx, cy]
    r = h / 2.0
    for i in range(steps+1):
        rx = r*cos(i*dtheta)
        ry = r*sin(i*dtheta)
        wheel += [cx+rx, cy+ry]
    
    colors = [v,v,v,1.0]*(len(wheel)//2)

    tex_coords = generate_coords(wheel, x, y, w, h)

    return {'id':'wheel',
            'len': len(wheel)//2,
            'mode': GL_TRIANGLE_FAN,
            'vertices': wheel,
            'colors': colors,
            'tex_coords': tex_coords
            }

def histogram(x, y, w, h, array, c, index=0):
    a = array

    xmin = a[:,0].min()
    ymin = a[:,1].min()
    xmax = a[:,0].max()
    ymax = a[:,1].max()
    xw = xmax - xmin
    yh = ymax - ymin

    a[:,0] = (a[:,0] - xmin) * (w/xw) + x
    a[:,1] = (a[:,1] - ymin) * (h/yh) + y

    # repeat and make every 2nd y coord equal to y, 
    # in order to make gl_quad_strip
    a = a.repeat(2, axis=0)
    a[1::2,1] = y

    hist = [x,y] + list(a.flat) + [x+w,y]
    hist = strip_fix(hist, 2)
    
    colors = c*(len(hist)//2)

    hist, colors = aajitter(hist, colors)


    return {'id':'additive_histogram%d' % index,
            'len': len(hist)//2,
            'mode': GL_QUAD_STRIP,
            'vertices': hist,
            'colors': colors,
            'data_update': 'stream'
            }


if __name__ == '__main__':
    np.set_printoptions(precision=3,suppress=True)
    roundoutline(10, 10, 80, 20, 2, [0.2]*4)
    
    
    
'''
def roundbase2(x, y, w, h, r):
    geo = []
    colors = []
    r = 6         # radius
    rsteps = 4      # radial divisions
    ch = h - 2*r    # central area height
    
    ar_theta = np.arange(rsteps+1) / float(rsteps) * pi/2.0
    corner = np.column_stack( (np.cos(ar_theta), np.sin(ar_theta)) ) * r
    
    corner_tl = corner.copy() + np.array([0,ch])
    corner_tr = corner.copy() + np.array([0,ch])
    corner_tl[:,0] = (r - corner_tl[:,0])   # flip tl corner
    corner_tr[:,0] = corner_tr[:,0] + w     # offset tr corner
    
    corner_bl = corner.copy()[::-1]
    corner_br = corner.copy()[::-1]
    corner_bl[:,0] = (r - corner_bl[:,0])   # flip bl corner
    corner_br[:,0] = corner_br[:,0] + w     # offset br corner
    corner_bl[:,1] = (r - corner_bl[:,1])   # flip y
    corner_br[:,1] = (r - corner_br[:,1])   # flip y

    # interleave l/r verts into QUAD_STRIP
    interleaved_t = np.column_stack((corner_tl, corner_tr)).reshape(-1,2)
    interleaved_b = np.column_stack((corner_bl, corner_br)).reshape(-1,2)
    interleaved = np.append( interleaved_b, interleaved_t, axis=0 )
    
    # offset
    interleaved += np.array([x,y])
    
    geo = quad_strip_fix(interleaved.flat, 2)
    colors = colors = [0.7]*3*(len(geo)//2)
    
    return {'mode':GL_QUAD_STRIP, 'vertices':geo, 'colors':colors}
'''    
