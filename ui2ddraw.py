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
    colors = colors = [0.7]*3*(len(geo)//2)
    
    return {'mode':GL_QUAD_STRIP, 'vertices':geo, 'colors':colors}
    
def fit(v, mi, mx):
    return (v  * (mx-mi)) + mi

#def fitc(v, mi, mx):
    

def roundbase(x, y, w, h, col1, col2):
    geo = []
    colors = []
    r = h/3.0         # radius
    rsteps = 3      # radial divisions
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

    geo = quad_strip_fix(geo, 2)
    
    # generate uv v coord from vertex y height
    geoarr = np.array(geo).reshape(-1,2)
    v = (geoarr[:,1] - y) / h          # v value based on vertex y height
    
    colors = np.repeat(v, 3).reshape(-1,3)
    colors = fit(colors, np.array(col1), np.array(col2))
    colors = list(colors.flat)
    
    return {'mode':GL_QUAD_STRIP, 'vertices':geo, 'colors':colors}
    
    
if __name__ == '__main__':
    np.set_printoptions(precision=3,suppress=True)
    roundbase(10, 10, 80, 20)