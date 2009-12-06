from layout import Shape

@package('charts')
class BottomHorizontalAxis(Shape):
    __slots__ = ('data', '_')

    def __init__(self, data, name, states):
        super().__init__(name, states)
        self.data = data

    def draw(self, width, height):
        super().draw(width, height)
        g = self.graphics
        g.lineStyle(1)
        g.moveTo(0, 0)
        g.lineTo(width, 0)
        for i in range(10):
            g.moveTo(int(i*width/10), 0)
            g.lineTo(int(i*width/10), 4)

@package('charts')
class LeftVerticalAxis(Shape):
    __slots__ = ('data', '_')

    def __init__(self, data, name, states):
        super().__init__(name, states)
        self.data = data

    def draw(self, width, height):
        super().draw(width, height)
        g = self.graphics
        g.lineStyle(1)
        g.moveTo(width, 0)
        g.lineTo(width, height)
        for i in range(10):
            g.moveTo(width-4, int(i*height/10))
            g.lineTo(width, int(i*height/10))

