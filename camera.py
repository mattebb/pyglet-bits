import platform
import math
from math import pi, sin, cos

import euclid
from euclid import Vector3, Point3

import pyglet
from pyglet.window import key
from pyglet.window import mouse
from pyglet.gl import *

keys = key.KeyStateHandler()

class CameraHandler(object):
    def __init__(self, window, camera):
        self.camera = camera
        self.window = window

        
        window.push_handlers(keys)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        
        if platform.system() != 'Darwin':
            dy = -dy

        if modifiers & pyglet.window.key.MOD_SHIFT:
            if buttons & mouse.RIGHT:
                self.camera.fov -= dx
                if self.camera.fov < 5.:
                    self.camera.fov = 5.
                elif self.camera.fov > 150:
                    self.camera.fov = 150
            
                winsize = self.window.get_size()
                self.camera.view_update(winsize[0], winsize[1])
                return pyglet.event.EVENT_HANDLED

        elif keys[key.SPACE]:
            if buttons & mouse.LEFT:
                s = 0.0075
                self.camera.phi += s * dx
                self.camera.theta -= s * dy
                if self.camera.theta > pi:
                    self.camera.theta = pi
                elif self.camera.theta < 0.0001:
                    self.camera.theta = 0.0001
                self.camera.update_location()
                
            if buttons & mouse.RIGHT:
                self.camera.radius += 0.01 * -dx
                if self.camera.radius < 0:
                    self.camera.radius = 0
                self.camera.update_location()
            
            if buttons & mouse.MIDDLE:
                s = 0.01
                self.camera.center[1] += s * dy
                
                phi = self.camera.phi + pi*0.5
                self.camera.center[0] += cos(phi) * s * dx
                self.camera.center[2] += sin(phi) * s * dx
                self.camera.update_location()
            
            return pyglet.event.EVENT_HANDLED

    def on_resize(self, width, height):
        self.camera.view_update(width, height)
        #return pyglet.event.EVENT_HANDLED


class Camera(object):

    def __init__(self, window):
        self.phi = pi / 2.0
        self.theta = pi * 0.4
        self.radius = 5.
        self.fov = 50.
        self.clipnear = 0.1
        self.clipfar = 1000
        
        self.center = Vector3(0,0,0)
        self.up = Vector3(0,1,0)

        self.loc = Vector3(0,0,0)
        self.update_location()
        
        self.needs_update = False

        self.window = window
        handlers = CameraHandler(window, self)
        window.push_handlers(handlers)

    def update_location(self):
        eyeX = self.radius * cos(self.phi) * sin(self.theta) + self.center[0]
        eyeY = self.radius * cos(self.theta)                 + self.center[1]
        eyeZ = self.radius * sin(self.phi) * sin(self.theta) + self.center[2]
        self.loc = Vector3(eyeX, eyeY, eyeZ)
        
    def project_ray(self, px, py):
        cam_view = (self.center - self.loc).normalize()
        
        self.cam_h =  cam_view.cross(self.up).normalize()
        self.cam_v = -1 * cam_view.cross(self.cam_h).normalize()
        
        half_v = math.tan(math.radians(self.fov)*0.5) * self.clipnear
        win = self.window.get_size()
        aspect = win[0] / float(win[1])
        half_h = half_v * aspect
        
        # mouse to ndc
        nx = (px - win[0]*0.5) / (win[0]*0.5)
        ny = (py - win[1]*0.5) / (win[1]*0.5)
        
        self.cam_h *= half_h
        self.cam_v *= half_v

        click = self.loc + (cam_view*self.clipnear)  + (nx * self.cam_h) + (ny * self.cam_v)

        '''
        modelview = (GLdouble * 16)()
        projection = (GLdouble * 16)()
        view = (GLint * 4)()
        
        glGetDoublev (GL_MODELVIEW_MATRIX, modelview);
        glGetDoublev (GL_PROJECTION_MATRIX, projection);
        glGetIntegerv( GL_VIEWPORT, view );
        
        wx,wy,wz = GLdouble(),GLdouble(),GLdouble() 
        gluUnProject(px, py, self.clipnear, modelview, projection, view, wx, wy, wz)
        click = Vector3(wx.value, wy.value, wz.value)
        '''
        dir = (click - self.loc).normalize()
        return click, dir
    
    def view_update(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, width / float(height), self.clipnear, self.clipfar)
        glMatrixMode(GL_MODELVIEW)
