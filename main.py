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
pyglet.options['debug_gl'] = True
#pyglet.options['debug_graphics_batch'] = True
#pyglet.options['debug_gl_trace'] = True
#pyglet.options['debug_gl_trace_args'] = True
from pyglet.gl import *

def init(): 
    from euclid import Vector3, Point3, Matrix4

    import ui2d

    from parameter import Parameter, Color3
    from camera import Camera
    from object3d import Scene
    
    def setup():
        # One-time GL setup
        glClearColor(0.35, 0.35, 0.35, 1)

    window = pyglet.window.Window(900, 400, resizable=True)
    scene = Scene()
    scene.camera = Camera(window)
    pyglet.clock.schedule(scene.update)
    
    setup()
 
    ui = ui2d.Ui(window, layoutw=0.2)
    ui.control_types['numeric'] += [Point3, Vector3]
    ui.control_types['color'] +=  [Color3]

    # load ptc objects from cmd line
    import ptc
    from ptc import Ptc
    import sys

    scene.pointclouds = []
    for filename in sys.argv[1:]:
        pointcloud = Ptc(scene, filename)
        scene.pointclouds.append( pointcloud )
        layout = ui.layout.addLayout(bg=True)
        layout.addParameter(ui, pointcloud.visible, title=filename)
        layout.addLabel(ui, title='%d pts'%pointcloud.numparts)
        layout.addParameter(ui, pointcloud.decimate)
        layout.addControl(ui, object=pointcloud, attr="translate")

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
    
    #scene.camera.fieldofview = Parameter(object=scene.camera, attr="fov", update=scene.camera.update_projection, vmin=5, vmax=150)
    #layout.addParameter(ui, scene.camera.fieldofview)
    layout.addParameter(ui, scene.frame)
    #ui.layout.print_r()

    

    # Event handlers
    window.push_handlers(scene)
    window.push_handlers(ptch)

    pyglet.app.run()

    # import cProfile
    # cProfile.run('pyglet.app.run()', '/tmp/pyprof')
    # import pstats
    # stats = pstats.Stats('/tmp/pyprof')
    # stats.sort_stats('time')
    # stats.print_stats(50)

    '''
    print 'INCOMING CALLERS:'
    stats.print_callers(25)
    print 'OUTGOING CALLEES:'
    stats.print_callees(25)
    '''

if __name__ == "__main__":
    init()