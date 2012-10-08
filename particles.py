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

@window.event
def on_mouse_press(x, y, buttons, modifiers):
    return
    if buttons & mouse.LEFT:
        click, dir = camera.project_ray(x, y)
        #cross = Ray(click, dir, 20)
        particles.intersect(click, dir)


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

#partgroup = ParticlesGroup()
#particles = Particles(2, 3, batch, group=partgroup)
