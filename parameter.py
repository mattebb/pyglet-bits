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

        if object != None and attr != '':
            if not hasattr(object, attr):
                raise ValueError("Invalid attribute provided: %s" % attr)
            self.storage = self.EXTERNAL
            self.object = object
            self.attr = attr
            self.title = self.attr.capitalize()
            self.type = type(getattr(self.object, self.attr))
        else:
            self.storage = self.INTERNAL
            self.param_storage = ParameterStorage(default)
            self.object = self.param_storage
            self.attr = "data"
            self.title = title
            self.type = type(self.param_storage.data)

        self.min = vmin
        self.max = vmax
        self.enum = enum
        self.subtype = subtype

        self.update = update

        self.len = attr_len(getattr(self.object, self.attr))
        
        self.needs_redraw = False

    def getval(self, sub=None):
        attr = getattr(self.object, self.attr)
        
        if self.len > 1 and sub is not None:
            return attr[sub]
        else:
            return attr
    
    def limited(self, val, newval):
        if type(val) in ('float', 'int'):
            return min(self.max, max(self.min, newval))
        else:
            return newval
    
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
    #def __get__(self, instance, owner):
    #    return instance

    # def __getattribute__(self, name):
    #     if name == 'param':
    #         return self
    #     else:
    #         return self.__dict__[name]

    # @property
    # def val(self):
    #     return self.getval()

    # @val.setter
    # def setv(self, value):
    #     self.setval(value)

    # def __getitem__(self, key):
    #     return self.getval(sub=key)

    # def __setitem__(self, key, value):
    #     self.setval(value, sub=key)
'''