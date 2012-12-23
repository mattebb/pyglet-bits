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




# XXX Move somewhere else
import euclid
class Color3(euclid.Vector3):
    pass

class Histogram(object):
    def __init__(self):
        self.arrays = []
        self.min = 0
        self.max = 1


def attr_len(attr):
    # if attr is subscriptable
    if hasattr(attr, "__getitem__"):
        return len(attr)
    else:
        return 1


class ParameterStorage(object):
    def __init__(self, default):
        self.data = default

class Parameter(object):
    INTERNAL = 0
    EXTERNAL = 1
    
    def __init__(self, object=None, attr='', enum=None, subtype=None, update=None, title='', default=None, vmin=0.0, vmax=1.0):

        self.title = title
        
        self.data = default
        self.type = type(self.data)
        self.len = attr_len(self.data)

        self.min = vmin
        self.max = vmax
        self.enum = enum
        self.subtype = subtype

        self.values = pv(self)
        self.update = update
        self.needs_redraw = False
        

    def limited(self, val, newval):
        if type(val) in ('float', 'int'):
            return min(self.max, max(self.min, newval))
        else:
            return newval
    @property
    def value(self):
        return self.data

    @value.setter
    def value(self, value):
        self.data = self.limited(self.data, value)
        self.param_edited()

    def param_edited(self):
        self.needs_redraw = True
        if self.update is not None:
            self.update()

    '''
    def getval(self, sub=None):
        attr = getattr(self.object, self.attr)
        
        if self.len > 1 and sub is not None:
            return attr[sub]
        else:
            return attr
    

    
    def setval(self, newval, sub=None):
        attr = getattr(self.object, self.attr)

        if self.len > 1 and sub is not None:
            attr[sub] = self.limited( attr[sub], newval )
        else:
            attr = self.limited(attr, newval)
        
        self.needs_redraw = True

        setattr(self.object, self.attr, attr)
        
        if self.update is not None:
            self.update()
    '''

class pv(object):

    def __getitem__(self, key):
        if hasattr(self.param.data, "__getitem__") and len(self.param.data) > 0:
            return self.param.data.__getitem__(key)
        else:
            return self.param.data

    def __setitem__(self, key, value):
        if hasattr(self.param.data, "__setitem__") and len(self.param.data) > 0:
            self.param.data.__setitem__(key, value)
        else:
            self.param.data = value
        self.param.param_edited()

    def __init__(self, param):
        self.param = param
