from flash.display import Sprite, Shape as BaseShape
from flash.events import Event
from flash.display import StageAlign, StageScaleMode
from string import repr

@package('layout')
class WidgetConflict(Error):
    def __init__(self, message):
        super().__init__(message)

@package('layout')
class Rect:
    __slots__ = ('x', 'y', 'width', 'height')
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __repr__(self):
        return 'Rect({x}, {y}, {width}, {height})'.format(self)

@package('layout')
class Rel:
    __slots__ = ('relx', 'rely', 'offx', 'offy', 'tox', 'toy')
    def __init__(self, relx, rely, tox=None, toy=None, offx=0, offy=0):
        self.relx = relx
        self.rely = rely
        if tox:
            self.tox = tox
        else:
            self.tox = None
        if toy:
            self.toy = toy
        else:
            self.toy = None
        self.offx = offx
        self.offy = offy

@package('layout')
class Constraint:
    __slots__ = ('alignx', 'aligny', 'minx', 'miny', 'maxx', 'maxy')
    def __init__(self, alignx=0, aligny=0, minx=None, miny=None,
        maxx=None, maxy=None):
        self.alignx = alignx
        self.aligny = aligny
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy

@package('layout')
class State:
    __slots__ = ('name', 'rel1', 'rel2', 'constraint')
    re = RegExp(r'''^
        (\w+) \:
        (?:<(\w*)(?::(\w+))?>)?
        \((?:<(\w*)(?::(\w+))?>)?
            (\d+|\d*\.\d+),(\d+|\d*\.\d+) (?:([+-]\d+)([+-]\d+)?)?\) -
        \((?:<(\w*)(?::(\w+))?>)?
            (\d+|\d*\.\d+),(\d+|\d*\.\d+) (?:([+-]\d+)([+-]\d+)?)?\)
        (?: \* \((\d+|\d*\.\d+) , (\d+|\d*\.\d+)\) )?
        (?: \[(\d*)(?:(-)(\d*))? , (\d*)(?:(-)(\d*))?\] )?
        $''', 'x')
    def __init__(self, name, rel1, rel2, constraint=None):
        self.name = name
        self.rel1 = rel1
        self.rel2 = rel2
        self.constraint = constraint

    @classmethod
    def parse(cls, string):
        val = cls.re.exec(string)
        if not val:
            raise Error("Wrong state expression {!r}".format(string))
        _, statename, globrelx, globrely, \
            rel1tox, rel1toy, rel1x, rel1y, rel1offx, rel1offy, \
            rel2tox, rel2toy, rel2x, rel2y, rel2offx, rel2offy, \
            alignx, aligny, \
            minx, xc, maxx, miny, yc, maxy = val
        if alignx or aligny or minx or maxx or miny or maxy:
            constraint = Constraint(
                float(alignx) if alignx else None,
                float(aligny) if aligny else None,
                int(minx) if minx else None,
                int(miny) if miny else None,
                (int(maxx) if maxx else None) if xc else (int(minx) if minx else None),
                (int(maxy) if maxy else None) if yc else (int(miny) if miny else None),
                )
        else:
            constraint = None
        return cls(statename,
            Rel(float(rel1x), float(rel1y),
                rel1tox or globrelx or None,
                rel1toy or rel1tox or globrely or globrelx or None,
                rel1offx and int(rel1offx) or 0, rel1offy and int(rel1offy) or 0),
            Rel(float(rel2x), float(rel2y),
                rel2tox or globrelx or None,
                rel2toy or rel2tox or globrely or globrelx or None,
                rel2offx and int(rel2offx) or 0, rel2offy and int(rel2offy) or 0),
            constraint)

@package('layout')
class Widget(Sprite):
    __slots__ = ('name', 'state', 'states', 'bounds')

    def __init__(self, name, states):
        self.name = name
        self.states = states
        self.state = states['normal']
        self.bounds = Rect(0, 0, 0, 0)

    def update_size(self):
        b = self.bounds
        self.x = b.x
        self.y = b.y
        self.draw(b.width, b.height)

    def draw(self, width, height):
        self.graphics.clear()

@package('layout')
class Shape(BaseShape):
    __slots__ = ('name', 'state', 'states', 'bounds')

    def __init__(self, name, states):
        self.name = name
        self.states = states
        self.state = states['normal']
        self.bounds = Rect(0, 0, 0, 0)

    def update_size(self):
        b = self.bounds
        self.x = b.x
        self.y = b.y
        self.draw(b.width, b.height)

    def draw(self, width, height):
        self.graphics.clear()

@package('layout')
class Layout:
    __slots__ = ('widgets', 'order', 'mapping')
    def __init__(self, widgets):
        self.widgets = widgets # order is z-buffer order
        self.order, self.mapping = self._sort(widgets)

    def realize(self, sprite, width, height):
        for i in values(self.widgets):
            sprite.addChild(i)
        self.mapping[None] = {'bounds':Rect(0, 0, width, height)}
        self._resize()

    def update_size(self, width, height):
        n = self.mapping[None].bounds
        if n.width != width or n.height != height:
            n.width = width
            n.height = height
            self._resize()

    def _sort(self, widgets):
        deps = {}
        mapping = {}
        for w in values(widgets):
            mapping[w.name] = w
            for s in values(w.states):
                wdeps = deps[w.name]
                for t in values([s.rel1.tox, s.rel1.toy,
                                 s.rel2.tox, s.rel2.toy]):
                    if bool(wdeps) and wdeps.indexOf(t) >= 0:
                        raise WidgetConflict(
                            "Conflict between ``{}'' and ``{}'' at state ``{}''"
                            .format(t, w.name, s.name))
                    l = deps[t]
                    if not l:
                        deps[t] = [w.name]
                    else:
                        l.push(w.name)
        tmp = deps[None].concat()
        for i in values(tmp):
            for j in values(deps[i]):
                tmp.push(j)
        traversed = {}
        res = []
        for i in range(tmp.length-1, -1, -1):
            n = tmp[i]
            if not traversed[n]:
                res.push(n)
                traversed[n] = True
        res.reverse()
        if res.length != widgets.length:
            raise Error("AssertionError: {!r} {!r}".format(res, widgets))
        rres = []
        for i in values(res):
            rres.push(mapping[i])
        return [rres, mapping]

    def _resize(self):
        for widget in values(self.order):
            s = widget.state
            rel1 = s.rel1
            rel2 = s.rel2
            rel1ox = self.mapping[rel1.tox].bounds
            rel1oy = self.mapping[rel1.toy].bounds
            rel2ox = self.mapping[rel2.tox].bounds
            rel2oy = self.mapping[rel2.toy].bounds
            l = rel1ox.x + rel1ox.width*rel1.relx
            t = rel1oy.y + rel1oy.height*rel1.rely
            if rel1.offx:
                l += rel1.offx
            if rel1.offy:
                t += rel1.offy
            r = rel2ox.x + rel2ox.width*rel2.relx
            b = rel2oy.y + rel2oy.height*rel2.rely
            if rel2.offx:
                r += rel2.offx
            if rel2.offy:
                b += rel2.offy
            w = r-l
            ow = w
            h = b-t
            oh = h
            cons = s.constraint
            if cons:
                if isinstance(cons, str):
                    raise Error('{!r}'.format(cons))
                if cons.minx != None and cons.minx >= 0:
                    w = max(w, cons.minx)
                if cons.miny != None and cons.miny >= 0:
                    h = max(h, cons.miny)
                if cons.maxx != None and cons.maxx >= 0:
                    w = min(w, cons.maxx)
                if cons.maxy != None and cons.maxy >= 0:
                    h = min(h, cons.maxy)
                if w != ow and not isNaN(cons.alignx):
                    l = l + (ow-w)*cons.alignx
                if h != oh and not isNaN(cons.aligny):
                    t = t + (oh-h)*cons.aligny
            bounds = widget.bounds
            bounds.x = int(l)
            bounds.y = int(t)
            bounds.width = int(w+0.5)
            bounds.height = int(h+0.5)
            widget.update_size()

@package('layout')
class TopLevel(Sprite):
    def __init__(self):
        stage = self.stage
        stage.align = StageAlign.TOP_LEFT
        stage.scaleMode = StageScaleMode.NO_SCALE
        self.layout.realize(self, stage.stageWidth, stage.stageHeight)
        stage.addEventListener(Event.RESIZE, self.onresize)

    def onresize(self, event):
        self.layout.update_size(self.stage.stageWidth, self.stage.stageHeight)
