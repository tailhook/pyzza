from layout import TopLevel, RoundRect, Widget, Layout, State, Rel, Constraint
from string import repr
from flash.display import Shape
from game import Frame, Keys

level = """
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
Xg....................................gX
X.XX.XXXXX.XX.XXX.XXXX.XXX.XX.XXXXX.XX.X
X.XX.XXXXX.XX.XXX.XXXX.XXX.XX.XXXXX.XX.X
X.XX.XXXXX.XX.XXX.XXXX.XXX.XX.XXXXX.XX.X
X.XX.......XX.XXX.XXXX.XXX.XX.......XX.X
X.XX.X.XXX.XX.XXX......XXX.XX.XXX.X.XX.X
X.XX.X.XXX.XX.XXX.XXXX.XXX.XX.XXX.X.XX.X
X.XX.X.XXX.XX.XXX.XXXX.XXX.XX.XXX.X.XX.X
X......................................X
X.XX.X.XXX.XX.XXX.XXXX.XXX.XX.XXX.X.XX.X
X.XX.X.XXX.XX.XXX.XXXX.XXX.XX.XXX.X.XX.X
X.XX.X.XXX.XX.XXX.c....XXX.XX.XXX.X.XX.X
X.XX.......XX.XXX.XXXX.XXX.XX.......XX.X
X.XX.XXXXX.XX.XXX.XXXX.XXX.XX.XXXXX.XX.X
X.XX.XXXXX.XX.XXX.XXXX.XXX.XX.XXXXX.XX.X
X.XX.XXXXX.XX.XXX.XXXX.XXX.XX.XXXXX.XX.X
Xg....................................gX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
"""

class Ghost(Shape):
    __slots__ = ('fx', 'fy')

    def __init__(self, x, y):
        self.fx = x
        self.fy = y

    def draw(self, width, height):
        g = self.graphics
        g.moveTo(width/4, height/4)
        g.lineTo(width*3/4, height/4)
        g.lineTo(width*3/4, height*3/8)
        g.lineTo(width/2, height*3/8)
        g.lineTo(width/2, height*5/8)
        g.lineTo(width*3/4, height*5/8)
        g.lineTo(width*3/4, height*3/4)
        g.lineTo(width/4, height*3/4)

class Meal(Shape):
    __slots__ = ('fx', 'fy', 'amount')
    def __init__(self, x, y, amount=10):
        self.fx = x
        self.fy = y
        self.amount = amount
    def draw(self, width, height):
        g = self.graphics
        g.clear()
        g.beginFill(0xFF0000)
        g.drawCircle(width/2, height/2, min(width, height)/4)
        g.endFill()

class Pacman(Shape):
    __slots__ = ('fx', 'fy')
    def __init__(self, x, y):
        self.fx = x
        self.fy = y

    def start(self):
        Keys.register(Keys.LEFT, 'pacman_left')
        Keys.register(Keys.RIGHT, 'pacman_right')
        Keys.register(Keys.DOWN, 'pacman_down')
        Keys.register(Keys.UP, 'pacman_up')
        Frame.attach(self.frame)

    def stop(self):
        Frame.detach(self.frame)

    def frame(self, delta):
        if Keys.keys.pacman_left:
            self.x -= delta*50
        if Keys.keys.pacman_right:
            self.x += delta*50
        if Keys.keys.pacman_up:
            self.y -= delta*50
        if Keys.keys.pacman_down:
            self.y += delta*50

    def draw(self, width, height):
        g = self.graphics
        g.clear()
        g.beginFill(0xFFFF00)
        g.lineStyle(1, 0xFF0000)
        g.moveTo(width/4, height/4)
        g.lineTo(width*3/4, height/4)
        g.lineTo(width*3/4, height*3/8)
        g.lineTo(width/2, height*3/8)
        g.lineTo(width/2, height*5/8)
        g.lineTo(width*3/4, height*5/8)
        g.lineTo(width*3/4, height*3/4)
        g.lineTo(width/4, height*3/4)
        g.endFill()

class Wall:
    __slots__ = ('fx', 'fy')
    def __init__(self, x, y):
        self.fx = x
        self.fy = y
    def draw(self, graph, x, y, width, height):
        graph.beginFill(0x808080)
        graph.drawRect(x, y, width, height)
        graph.endFill()

class Field(Widget):
    def __init__(self, data, name, states):
        super().__init__(name, states)
        self.ghosts = []
        self.pacman = None
        self.walls = {}
        self.meals = {}
        self.wallsprite = Shape()
        self.wallsprite.cacheAsBitmap = True
        self.addChild(self.wallsprite)
        self.field_width = 0
        self.field_height = 0
        y = 0
        for line in values(data.split('\n')):
            x = 0
            for i in range(line.length):
                c = line.charAt(i)
                if ' \n\t\r'.indexOf(c) >= 0:
                    continue
                if c == '.':
                    self.meals['p{}_{}'.format(x, y)] = Meal(x, y)
                elif c == 'g':
                    self.ghosts.push(Ghost(x, y))
                elif c == 'c':
                    self.pacman = Pacman(x, y)
                elif c == 'X':
                    self.walls['p{}_{}'.format(x, y)] = Wall(x, y)
                x += 1
                self.field_width = max(x, self.field_width)
            if x:
                y += 1
                self.field_height = y
        for m in values(self.meals):
            self.addChild(m)
        for g in values(self.ghosts):
            self.addChild(g)
        self.addChild(self.pacman)

    def draw(self, width, height):
        super().draw(width, height)
        w = width/self.field_width
        h = height/self.field_height
        # drawing walls
        wg = self.wallsprite.graphics
        wg.clear()
        for wall in values(self.walls):
            wall.draw(wg, w*wall.fx, h*wall.fy, w, h)
        # drawing other objects
        for m in values(self.meals):
            m.x = w*m.fx
            m.y = h*m.fy
            m.draw(w, h)
        for g in values(self.ghosts):
            g.x = w*g.fx
            g.y = h*g.fy
        p = self.pacman
        p.x = w*p.fx
        p.y = h*p.fy
        self.pacman.draw(w, h)

    def start(self):
        self.pacman.start()

@package('pacman')
class Main(TopLevel):
    def __init__(self):
        self.layout = Layout([
            Field(level, 'field', {
                'normal': State.parse(
                'normal:(0,0)-(1,1)'),
                }),
            ])
        super().__init__()
        Frame.start(self, True)
        Keys.start(self.stage)
        self.layout.mapping.field.start()
