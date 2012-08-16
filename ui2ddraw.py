from pyglet.gl import *

import math
from math import sin, cos, pi

import numpy as np

np.set_printoptions(precision=3,suppress=True)

def quad_strip_fix(sequence, size):
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


def roundbase2(x, y, w, h):
    geo = []
    colors = []
    r = 6         # radius
    rsteps = 3      # radial divisions
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
    
    #geo = [x,y, x+w,y, x,y+h, x+w,y+h ]

    colors = colors = [0.7]*3*(len(geo)//2)

    return {'mode':GL_QUAD_STRIP, 'vertices':geo, 'colors':colors}
    
    
if __name__ == '__main__':
    np.set_printoptions(precision=3,suppress=True)
    roundbase2(10, 10, 50, 20)

def roundbase(x, y, w, h):
    geo = []
    colors = []
    r = 6           # radius
    rsteps = 2      # radial divisions
    ch = h - 2*r    # central area height
    
    # draw rounded box, horizontal quads, bottom to top
    
    # bottom rounded region
    for i in range(rsteps):
        theta = pi/2.0 * i/(float(rsteps))
        theta2 = pi/2.0 * (i+1)/(float(rsteps))
        
        yr = cos(theta)*r
        xr = sin(theta)*r
        yr2 = cos(theta2)*r
        xr2 = sin(theta2)*r
        
        # bottom left, bottom right
        geo += [x+r-xr, y+r-yr,     x+w-r+xr, y+r-yr]
        # top right, bottom left
        geo += [x+w-r+xr2, y+r-yr2,   x+r-xr2, y+r-yr2]
    
    # middle quad
    geo += [x, y+r,         x+w, y+r]   # bl, br
    geo += [x+w, y+h-r,     x, y+h-r]  # tr, tl
    
    colors = [0.4]*(len(geo)/2)
    
    return {'vertices':geo, 'colors':colors}