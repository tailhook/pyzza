@package('charts')
class RectangleData:
    __slots__ = ('minx', 'maxx', 'miny', 'maxy', 'data')
    def __init__(self, data):
        self.data = data
        self.analyze(data)

    def analyze(self, data):
        min = []
        max = []
        for a in values(data[0]):
            min.push(a)
            max.push(a)
        for row in values(data):
            i = 0
            for val in values(row):
                if val < min[i]:
                    min[i] = val
                if val > max[i]:
                    max[i] = val
                i += 1
        self.minx = min[0]
        self.maxx = max[0]
        maxy = max[1]
        miny = min[1]
        for i in range(2, min.length):
            if max[i] > maxy:
                maxy = max[i]
            if min[i] < miny:
                miny = min[i]
        self.miny = miny
        self.maxy = maxy

    def __repr__(self):
        return "<RectangleData x:[{minx}:{maxx}], y:[{miny}:{maxy}], data:{data!r}>".format(self)
