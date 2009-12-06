from layout import Shape
from string import repr

@package('charts')
class LineChart(Shape):

    def __init__(self, data, style, name, states):
        self.data = data
        self.style = style
        super().__init__(name, states)

    def draw(self, width, height):
        super().draw(width, height)
        g = self.graphics
        dt = self.data.data
        xk = width/(self.data.maxx - self.data.minx)
        xb = self.data.minx
        yk = height/(self.data.maxy - self.data.miny)
        yb = self.data.miny
        for yi in range(1, dt[0].length):
            i = 0
            g.lineStyle(2, self.style.data_series_colors[yi-1])
            for val in values(dt):
                if i:
                    g.lineTo(int((val[0]-xb)*xk), int(height-(val[yi]-yb)*yk))
                else:
                    g.moveTo((val[0]-xb)*xk, height-(val[yi]-yb)*yk)
                i += 1
