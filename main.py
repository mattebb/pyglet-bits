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
# Disable error checking for increased performance
pyglet.options['debug_gl'] = False
#pyglet.options['debug_graphics_batch'] = True
#pyglet.options['debug_gl_trace'] = True
#pyglet.options['debug_gl_trace_args'] = True
#from pyglet.gl import *

def init():
    
    from euclid import Vector3, Point3, Matrix4

    #import ui2d
    from ui2d import Ui, UiLayout, UiControls

    from parameter import Parameter, Color3
    from camera import Camera
    from object3d import Scene, filename_frame
    import os
    import sys

    window = pyglet.window.Window(1024, 500, resizable=True)

    scene = Scene()
    scene.camera = Camera(window)
    pyglet.clock.schedule(scene.update)
    
    pyglet.gl.glClearColor(0.32, 0.32, 0.32, 1)
 
    ui = Ui(window, layoutw=0.25)
    ui.control_types['numeric'] += [Point3, Vector3]
    ui.control_types['color'] +=  [Color3]

    # load ptc objects from cmd line
    import ptc
    from ptc import Ptc
    import re

    # find first frame of sequences
    maxframe = 0
    minframe = 9999999999

    for filename in sys.argv[1:]:
        f_re = re.search('\.([0-9]+)\.', filename)
        if f_re is None:
            continue
        f = int(f_re.group(1))
        minframe = f

        for i in xrange(f, f+10000):
            #fi = filename_frame(filename, i)
            fi = re.sub('(.+\.)[0-9]+(\..+)', '\g<1>%04d\g<2>'%i, filename)
            
            if ptc.valid_file(fi):
                maxframe = i
            else:
                break

    scene.sframe.value = minframe
    scene.eframe.value = maxframe
    scene.frame.value =  minframe


    scene.pointclouds = []
    for filename in sys.argv[1:]:
        pointcloud = Ptc(scene, filename)
        scene.pointclouds.append( pointcloud )
        layout = ui.layout.addLayout(bg=True)
        layout.addParameter(ui, pointcloud.visible, title=filename[-28:])
        
        layout.addParameter(ui, pointcloud.decimate)
        layout.addLabel(ui, param=pointcloud.num_particles)
        
        layout.addLabel(ui, title=' ') # Separator

        layout.addParameter(ui, pointcloud.attributes)
        layout.addParameter(ui, pointcloud.show_statistics)
        layout.addLabel(ui, param=pointcloud.attr_stats)
        layout.addParameter(ui, pointcloud.histogram)
        
        ui.layout.addLabel(ui, title=' ') # Separator
    
    ptch = ptc.PtcHandler(scene, window)
    scene.calculate_bounds()
    scene.camera.focus(scene)

    layout = ui.layout.addLayout(bg=True)
    # ptc class variables, global
    layout.addParameter(ui, Ptc.ptsize)
    layout.addParameter(ui, Ptc.gamma)
    layout.addParameter(ui, Ptc.exposure)
    layout.addParameter(ui, Ptc.hueoffset)
    
    #scene.camera.fieldofview = Parameter(object=scene.camera, attr="fov", subtype=UiControls.ANGLE, update=scene.camera.update_projection, vmin=0.087, vmax=2.618)
    #layout.addParameter(ui, scene.camera.fieldofview)
    
    ui.layout.addLabel(ui, title=' ') # Separator

    layout = ui.layout.addLayout(bg=True)
    # horz = layout.addLayout(bg=False, style=UiLayout.HORIZONTAL)
    # def sframe():
    #     scene.frame.value = scene.sframe.value
    # def eframe():
    #     scene.frame.value = scene.eframe.value
    # horz.addControl(ui, func=sframe, title='<')
    # horz.addParameter(ui, scene.playback)
    # horz.addControl(ui, func=eframe, title='>')

    layout.addParameter(ui, scene.playback)
    layout.addParameter(ui, scene.sframe)
    layout.addParameter(ui, scene.eframe)
    layout.addParameter(ui, scene.frame)

    

    # Event handlers
    window.push_handlers(scene)
    window.push_handlers(ptch)

    

    '''
    print 'INCOMING CALLERS:'
    stats.print_callers(25)
    print 'OUTGOING CALLEES:'
    stats.print_callees(25)
    '''

if __name__ == "__main__":
    init()

    pyglet.app.run()

    # import cProfile
    # cProfile.run('pyglet.app.run()', '/tmp/pyprof')
    # import pstats
    # stats = pstats.Stats('/tmp/pyprof')
    # stats.sort_stats('time')
    # stats.print_stats(50)