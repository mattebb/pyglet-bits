from pyglet.gl import *

import math
from math import sin, cos, pi

import numpy as np

np.set_printoptions(precision=3,suppress=True)

def strip_fix(sequence, size):
    '''
    add degenerate verts at start and end to satisfy pyglet QUAD_STRIP handling
    '''
    l = list(sequence)
    return l[:size] + l + l[-size:]

    '''
    # add degenerate verts to numpy array
    #interleaved = np.insert(interleaved, 0, interleaved[0,:], axis=0)
    #last = interleaved[len(interleaved)-1,:]
    #interleaved = np.append(interleaved, [last], axis=0)
    '''

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

def fit(v, mi, mx):
    return (v  * (mx-mi)) + mi

def roundbase(x, y, w, h, r, col1, col2):
    geo = []
    colors = []
    r = h * 0.35         # radius
    rsteps = 2      # radial divisions
    ch = h - 2*r    # central area height
    
    # draw rounded box, horizontal quads, bottom to top
    for i in range(-rsteps,rsteps+1):
        theta = pi/2.0 * i/(float(rsteps))
        
        if i == 0:
            # central rect
            geo += [x, r+y,      r+x+w, r+y]
            geo += [x, r+y+ch,   r+x+w, r+y+ch]
        else:
            # rounded edges
            x2 = cos(theta)*r
            y0 = sin(theta)*r + r
            x1 = r - x2
            if i > 0:
                y0 += ch
            geo += [x1+x, y0+y,  x2+x+w, y0+y]

    geo = strip_fix(geo, 2)
    
    # generate uv v coord from vertex y height
    v = [ (gy-y)/h for gy in geo[1::2] ]    # vertex y = slice to find odd list items
    
    colors = np.repeat(v, 4).reshape(-1,4)
    colors = fit(colors, np.array(col1), np.array(col2))
    colors = list(colors.flat)
        
    return {'id':'roundbase',
            'len': len(geo)//2,
            'mode':GL_QUAD_STRIP,
            'vertices':geo,
            'colors':colors
            }
    

def roundoutline(x, y, w, h, r, col):
    data = roundbase(x, y, w, h, r, [0]*4, [0]*4)
    
    alpha = col[3]
    
    geo = data['vertices'][2:-2]
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
    
    return {'id':'roundoutline',
            'len': len(outline)//2,
            'mode':GL_LINES,
            'vertices':outline,
            'colors':colors
            }

if __name__ == '__main__':
    np.set_printoptions(precision=3,suppress=True)
    roundoutline(10, 10, 80, 20, 2, [0.2]*4)