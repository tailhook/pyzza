from layout import Shape

@package('layout')
class Poly(Shape):
    __slots__ = ('fillcolor', 'sequence')
    def __init__(self, name, fillcolor, seq, states):
        super().__init__(name, states)
        self.fillcolor = fillcolor
        self.sequence = seq

    def draw(self, w, h):
        g = self.graphics
        g.clear()
        for line in values(self.sequence):
            g.beginFill(self.fillcolor)
            g.moveTo(int(line[0][0]*w), int(line[0][1]*h))
            for idx in range(1, line.length):
                g.lineTo(int(line[idx][0]*w), int(line[idx][1]*h))
            g.endFill()

@package('layout')
class RoundRect(Shape):
    __slots__ = ('fillcolor', 'radius')
    def __init__(self, name, fillcolor, radius, states):
        super().__init__(name, states)
        self.fillcolor = fillcolor
        self.radius = radius

    def draw(self, width, height):
        g = self.graphics
        g.clear()
        g.beginFill(self.fillcolor)
        g.drawRoundRect(0, 0, width, height, self.radius, self.radius)
        g.endFill()
