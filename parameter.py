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
    
    def __init__(self, object=None, attr='', update=None, title='', default=None, vmin=0.0, vmax=1.0):

        if object != None and attr != '':
            if not hasattr(object, attr):
                raise ValueError("Invalid attribute provided: %s" % attr)
            self.storage = self.EXTERNAL
            self.object = object
            self.attr = attr
            self.title = self.attr.capitalize()
        else:
            self.storage = self.INTERNAL
            self.param_storage = ParameterStorage(default)
            self.object = self.param_storage
            self.attr = "data"
            self.title = title

        self.min = vmin
        self.max = vmax

        self.update = update

        self.len = attr_len(getattr(self.object, self.attr))
        self.type = type(getattr(self.object, self.attr))

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
        
        setattr(self.object, self.attr, attr)
        
        if self.update is not None:
            self.update()