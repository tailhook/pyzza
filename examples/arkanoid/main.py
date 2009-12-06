from flash.display import Sprite
from flash.display import StageAlign, StageScaleMode
from flash.events import Event, KeyboardEvent
from flash.text import TextField
from flash.utils import getTimer
from flash.geom import Matrix
from flash.display import GradientType, SpreadMethod
from game import Frame, Keys
from layout import TopLevel, Widget
from layout import State, Layout

class Ball(Sprite):
    def __init__(self, field):
        self.field = field
        self.graphics.beginFill(0xFF0000)
        self.graphics.drawCircle(-field.BALLRADIUS/2, -field.BALLRADIUS/2,
            field.BALLRADIUS)
        self.graphics.endFill()
        self.cacheAsBitmap = True
        self.radius = field.BALLRADIUS

    def initposition(self):
        self.pos_x = self.field.TOTALWIDTH/2
        self.pos_y = self.field.TOTALHEIGHT/2
        self.speed_x = 0
        self.speed_y = 200

    def start(self):
        self.initposition()
        Frame.attach(self.frame)

    def stop(self):
        Frame.detach(self.frame)
        self.speed_x = 0
        self.speed_y = 0

    def frame(self, delta):
        sx = self.speed_x*delta
        sy = self.speed_y*delta
        nx = self.pos_x + sx
        ny = self.pos_y + sy
        if nx < self.radius:
            self.pos_x = -nx + 2*self.radius
            self.speed_x = -self.speed_x
            self.speed_x *= 0.75
        elif nx > self.field.TOTALWIDTH - self.radius:
            self.pos_x = self.field.TOTALWIDTH*2 - 2*self.radius - nx
            self.speed_x = -self.speed_x
            self.speed_x *= 0.75
        else:
            self.pos_x = nx
        if ny < self.radius:
            self.pos_y = -ny + 2*self.radius
            self.speed_y = -self.speed_y
        elif ny > self.field.TOTALHEIGHT:
            self.initposition()
        else:
            self.pos_y = ny
        self.x = Math.round(self.pos_x)
        self.y = Math.round(self.pos_y)

class Racket(Sprite):
    def __init__(self, field):
        self.racket_width = 80
        self.field = field
        self.pos = 0.5

    def draw(self):
        field = self.field
        self.x = Math.round((field.TOTALWIDTH - self.racket_width)*self.pos)
        self.y = field.TOTALHEIGHT - field.BRICKHEIGHT - field.PADDING
        m = Matrix()
        m.createGradientBox(self.racket_width, field.BRICKHEIGHT,
            0, -self.racket_width/4, -field.BRICKHEIGHT/4)
        self.graphics.beginGradientFill(GradientType.RADIAL,
            [0xFFFFFF, 0x808080], #colors
            [1.0, 1.0], #alphas
            [0, 255], #ratios
            m, # transform matrix
            SpreadMethod.PAD)
        self.graphics.drawRoundRect(0, 0, self.racket_width,
            field.BRICKHEIGHT, field.BRICKHEIGHT, field.BRICKHEIGHT)
        self.graphics.endFill()
        m.createGradientBox(self.racket_width*3, field.BRICKHEIGHT*3,
            0, -self.racket_width/4, -field.BRICKHEIGHT/4)
        self.graphics.beginGradientFill(GradientType.RADIAL,
            [0xFFFFFF, 0x808080], #colors
            [1.0, 1.0], #alphas
            [0, 255], #ratios
            m, # transform matrix
            SpreadMethod.PAD)
        self.graphics.drawRoundRect(field.LINEWIDTH, field.LINEWIDTH,
            self.racket_width - field.LINEWIDTH*2,
            field.BRICKHEIGHT - field.LINEWIDTH*2,
            field.BRICKHEIGHT - field.LINEWIDTH,
            field.BRICKHEIGHT - field.LINEWIDTH)
        self.graphics.endFill()
        self.cacheAsBitmap = True

    def start(self):
        Frame.attach(self.frame)
        Keys.register(Keys.LEFT, 'racket_left')
        Keys.register(Keys.RIGHT, 'racket_right')

    def stop(self):
        Frame.detach(self.frame)

    def frame(self, delta):
        if delta:
            if Keys.keys.racket_left:
                self.speed -= delta
            elif Keys.keys.racket_right:
                self.speed += delta
            else:
                if Math.abs(self.speed) > 0.01:
                    self.speed *= Math.pow(0.01, delta)
                else:
                    self.speed = 0
            if self.speed:
                self.pos += self.speed*delta
                if self.pos < 0:
                    self.pos = 0
                elif self.pos > 1:
                    self.pos = 1
        self.x = Math.round((self.field.TOTALWIDTH-self.racket_width)*self.pos)

class Brick(Sprite):
    def __init__(self, field, brickdef):
        m = Matrix()
        fullw = field.BRICKWIDTH
        fullh = field.BRICKHEIGHT
        m.createGradientBox(fullw, fullh, 0, -fullw/4, -fullh/4)
        self.graphics.beginGradientFill(GradientType.RADIAL,
            [0xFFFFFF, brickdef.color], #colors
            [1.0, 1.0], #alphas
            [0, 255], #ratios
            m, # transform matrix
            SpreadMethod.PAD)
        self.graphics.drawRoundRect(0, 0, fullw, fullh, field.ROUND)
        self.graphics.endFill()
        m.createGradientBox(fullw*3, fullh*3, 0, -fullw/4, -fullh/4)
        self.graphics.beginGradientFill(GradientType.RADIAL,
            [0xFFFFFF, brickdef.color], #colors
            [1.0, 1.0], #alphas
            [0, 255], #ratios
            m, # transform matrix
            SpreadMethod.PAD)
        self.graphics.drawRoundRect(field.LINEWIDTH, field.LINEWIDTH,
            field.BRICKWIDTH-field.LINEWIDTH*2,
            field.BRICKHEIGHT-field.LINEWIDTH*2,
            field.ROUND-field.LINEWIDTH)
        self.graphics.endFill()
        self.cacheAsBitmap = True

    def hit(self): # die on first hit
        return True

class BrickDef:
    def __init__(self, color):
        self.color = color

class Level:
    def __init__(self, bricks, levelset):
        self.bricks = bricks
        self.levelset = levelset

    def populate(self, field):
        lines = {}
        y = 0
        for line in values(self.levelset.split('\n')):
            x = 0
            for i in range(line.length):
                c = line.charAt(i)
                if ' \n\t\r'.indexOf(c) >= 0:
                    continue
                if c == '.':
                    pass
                elif self.bricks[c]:
                    b = Brick(field, self.bricks[c])
                    field.add_brick(x, y, b)
                x += 1
            if x:
                y += 1

level1 = Level({
    'r': BrickDef(0xFF0000),
    'g': BrickDef(0x00FF00),
    'b': BrickDef(0x0000FF),
    },
    """
    rrrrggggggrrrr
    ggggbbbbbbgggg
    rrrrbbbbbbrrrr
    ggggbbbbbbgggg
    rrrrggggggrrrr
    """)

class Field(Widget):
    def __init__(self, level, name, states):
        super().__init__(name, states)
        self.init_const()
        self.ball = Ball(self)
        self.racket = Racket(self)
        self.bricks = {}
        self.drawn = False
        level1.populate(self)
        self.addChild(self.ball)
        self.addChild(self.racket)

    def start(self):
        self.racket.start()
        self.ball.start()
        Frame.attach(self.frame)

    def stop(self):
        Frame.detach(self.frame)
        self.ball.stop()
        self.racket.stop()

    def frame(self, delta):
        test = self.ball.hitTestObject
        if test(self.racket):
            self.ball.speed_y = -self.ball.speed_y
            if self.racket.speed:
                self.ball.speed_x += self.racket.speed*5
        bx = (self.ball.x - self.PADDING)
        bax = Math.floor((bx - self.BALLRADIUS) / self.BRICKWIDTH)
        bbx = Math.floor((bx + self.BALLRADIUS) / self.BRICKWIDTH)
        by = (self.ball.y - self.PADDING)
        bay = Math.floor((by - self.BALLRADIUS) / self.BRICKHEIGHT)
        bby = Math.floor((by + self.BALLRADIUS) / self.BRICKHEIGHT)
        for bkey in values([
                bax + ',' + bay,
                bax + ',' + bby,
                bbx + ',' + bay,
                bby + ',' + bby,
                ]):
            b = self.bricks[bkey]
            if not b: continue
            if test(b) and b.hit():
                del self.bricks[bkey]
                self.removeChild(b)

    def init_const(self):
        self.BALLRADIUS = 10
        self.PADDING = 20
        self.BRICKWIDTH = 40
        self.BRICKHEIGHT = 20
        self.ROUND = 10
        self.LINEWIDTH = 3

    def add_brick(self, x, y, brick):
        self.bricks[x + ',' + y] = brick
        brick.x = self.PADDING+self.BRICKWIDTH*x
        brick.y = self.PADDING+self.BRICKHEIGHT*y
        self.addChild(brick)

    def draw(self, width, height):
        self.TOTALWIDTH = width
        self.TOTALHEIGHT = height
        if not self.drawn:
            self._draw()
            self.drawn = True
            self.racket.draw()

    def _draw(self):
        self.graphics.lineStyle(2, 0x000000)
        self.graphics.drawRoundRect(0, 0,
            self.TOTALWIDTH, self.TOTALHEIGHT,
            self.ROUND, self.ROUND)

@package('arkanoid')
class Main(TopLevel):
    def __init__(self):
        Frame.start(self, True)
        Keys.start(self.stage)
        self.layout = Layout([
            Field(level1, 'field', {
                'normal': State.parse(
                'normal:(0,0)-(1,1)*(0.5,0.5)[560,400]'),
                }),
            ])
        super().__init__()
        self.layout.mapping.field.start()
