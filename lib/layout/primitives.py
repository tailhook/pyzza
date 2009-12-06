from layout import Shape, Widget
from flash.text.engine import TextBlock, TextElement

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

@package('layout')
class TextLine(Widget):
    __slots__ = ('format', 'text', 'textline')
    def __init__(self, format, text, name, states):
        self.format = format
        self.text = text
        super().__init__(name, states)

    def draw(self, width, height):
        if self.textline:
            self.removeChild(self.textline)
        tb = TextBlock()
        tb.content = TextElement(self.text, self.format)
        self.textline = tb.createTextLine(None, width)
        self.addChild(self.textline)

@package('layout')
class CenteredLine(TextLine):
    def __init__(self, format, text, name, states):
        super().__init__(format, text, name, states)
    def draw(self, width, height):
        super().draw(width, height)
        self.textline.x = int((width - self.textline.width)/2)
        self.textline.y = int((height - self.textline.height)/2)
