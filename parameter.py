def attr_len(attr):
    # if attr is subscriptable
    if hasattr(attr, "__getitem__"):
        return len(attr)
    else:
        return 1

class Parameter(object):
    def __init__(self, object=None, attr='', update=None):

        if not hasattr(object, attr):
            raise ValueError("Invalid attribute provided: %s" % attr)

        self.object = object
        self.attr = attr
        self.update = update

        self.title = self.attr.capitalize()

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