from psychopy import core, visual, gui, data, event
import numpy as np
wait = core.wait

FRAME_RATE = 60

def move_towards(pos, dest, dist):
    total = np.linalg.norm(pos - dest)
    frac = dist / total
    return (1 - frac) * pos + frac * dest

def shift(obj, x, y):
    if hasattr(obj, 'shift'):
        obj.shift(x, y)
    else:
        obj.setPos(obj.pos + np.array([x, y]))

class MultiShape(object):
    """One shape composed of multiple visual objects."""
    def __init__(self, *objects):
        self.objects = objects

    def setColor(self, x):
        for o in self.objects:
            o.setColor(x)

    def setAutoDraw(self, x):
        for o in self.objects:
            o.setAutoDraw(x)

    def setOpacity(self, x):
        for o in self.objects:
            o.setOpacity(x)

    def shift(self, x, y):
        for o in self.objects:
            shift(o, x, y)


def shape(f):
    def wrapper(self, *args, sub_shape=False, **kwargs):
        obj = f(self, *args, **kwargs)
        obj.setAutoDraw(kwargs.get('autoDraw', True))
        if not sub_shape:
            self.objects.append(obj)
        return obj
    return wrapper

class Graphics(object):
    def __init__(self, win):
        self.win = win
        self.animating = False
        self.objects = []

    def clear(self):
        for o in self.objects:
            o.setAutoDraw(False)

    def show(self):
        for o in self.objects:
            o.setAutoDraw(True)

    @shape
    def image(self, pos, image, size, path='images', **kws):
        return visual.ImageStim(self.win, image=path + '/' + image, pos=pos, size=(size, size))


    @shape
    def circle(self, pos, r=.05, lineColor='black', fillColor='white', lineWidth=2, **kws):
        return visual.Circle(self.win, radius=r, pos=pos, fillColor=fillColor, lineColor=lineColor, lineWidth=lineWidth, **kws)

    @shape
    def line(self, start, end, lineColor='black', lineWidth=4, **kws):
        return visual.Line(self.win, start=start, end=end, lineColor=lineColor, lineWidth=lineWidth, **kws)

    @shape
    def text(self, text, pos=(0,0), height=.03, color='black', **kws):
        return visual.TextStim(self.win, text, pos=pos, height=height, color=color, **kws)

    @shape
    def rect(self, pos, width, height, **kws):
    # Remove lineWidth from kws if it exists to avoid conflict
        if 'lineWidth' in kws:
            del kws['lineWidth']
        return visual.Rect(self.win, width, height, pos=pos, lineWidth=0, **kws)
    
    def animate(self, sec):
        self.animating = True
        total = round(sec * FRAME_RATE)
        for i in range(1,total+1):
            yield i / total
        self.animating = False

    def shift(self, x=0, y=0):
        for o in self.objects:
            shift(o, x, y)