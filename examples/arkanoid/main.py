from flash.display import Sprite
from flash.display import StageAlign, StageScaleMode
from flash.events import Event, KeyboardEvent
from flash.text import TextField
from flash.utils import getTimer
from flash.geom import Matrix
from flash.display import GradientType, SpreadMethod

class Ball(Sprite):
    def __init__(self, field):
        self.field = field
        self.graphics.beginFill(0xFF0000)
        self.graphics.drawCircle(0, 0, field.BALLRADIUS)
        self.graphics.endFill()
        self.cacheAsBitmap = True

    def start(self):
        self.pos_x = 0.5
        self.pos_y = 0.5
        self.speed_x = 0
        self.speed_y = 0.3

    def stop(self):
        self.speed_x = 0
        self.speed_y = 0

    def frame(self, delta):
        self.pos_x += self.speed_x*delta
        self.pos_y += self.speed_y*delta
        if self.pos_x < 0:
            self.pos_x = -self.pos_x
            self.speed_x = -self.speed_x
            self.speed_x *= 0.75
        elif self.pos_x > 1:
            self.pos_x = 2 - self.pos_x
            self.pos_x = -self.pos_x
            self.speed_x *= 0.75
        if self.pos_y < 0:
            self.pos_y = -self.pos_y
            self.speed_y = -self.speed_y
        elif self.pos_y > 1:
            self.start()
        self.x = Math.round(self.field.PADDING \
            + (self.field.TOTALWIDTH - self.field.PADDING*2)*self.pos_x)
        self.y = Math.round(self.field.PADDING \
            + (self.field.TOTALHEIGHT - self.field.PADDING*2)*self.pos_y)

class Racket(Sprite):
    def __init__(self, field):
        self.prepare_keys()
        self.racket_width = 80
        self.field = field
        self.pos = 0.5
        self.x = Math.round((field.TOTALWIDTH - self.racket_width)*self.pos)
        self.y = field.TOTALHEIGHT - field.BRICKHEIGHT - field.PADDING
        self.graphics.beginFill(0x0000FF)
        self.graphics.drawRoundRect(0, 0, self.racket_width,
            field.BRICKHEIGHT, field.ROUND)
        self.graphics.endFill()
        self.graphics.beginFill(0xB0B0B0)
        self.graphics.drawRoundRect(field.LINEWIDTH, field.LINEWIDTH,
            self.racket_width - field.LINEWIDTH*2,
            field.BRICKHEIGHT - field.LINEWIDTH*2,
            field.ROUND - field.LINEWIDTH)
        self.graphics.endFill()
        self.cacheAsBitmap = True

    def prepare_keys(self):
        self.keycodes = {
            '37': 'left',
            '39': 'right',
            }

    def start(self):
        self.keys = {}
        self.speed = 0
        self.stage.addEventListener(KeyboardEvent.KEY_DOWN, self.keydown)
        self.stage.addEventListener(KeyboardEvent.KEY_UP, self.keyup)

    def stop(self):
        self.stage.removeEventListener(KeyboardEvent.KEY_DOWN, self.keydown)
        self.stage.removeEventListener(KeyboardEvent.KEY_UP, self.keyup)
        del self.keys, self.speed

    def keydown(self, event):
        code = String(event.keyCode)
        if event.shiftKey:
            code = 's' + code
        if event.ctrlKey:
            code = 'c' + code
        if event.altKey:
            code = 'a' + code
        code = self.keycodes[code]
        if code:
            self.keys[code] = True

    def keyup(self, event):
        code = String(event.keyCode)
        if event.shiftKey:
            code = 's' + code
        if event.ctrlKey:
            code = 'c' + code
        if event.altKey:
            code = 'a' + code
        code = self.keycodes[code]
        if code:
            del self.keys[code]

    def frame(self, delta):
        if delta:
            if self.keys.left:
                self.speed -= 1.0*delta
            elif self.keys.right:
                self.speed += 1.0*delta
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
        self.x = Math.round(
            (self.field.TOTALWIDTH-self.racket_width
                - self.field.PADDING*2)*self.pos + self.field.PADDING)

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

@package('arkanoid')
class Field(Sprite):
    def __init__(self, width, height):
        #debug
        label = TextField()
        self.label = label
        self.addChild(label)
        #enddebug
        self.TOTALWIDTH = width
        self.TOTALHEIGHT = height
        self.init_const()
        self.draw()
        self.ball = Ball(self)
        self.racket = Racket(self)
        self.bricks = {}
        level1.populate(self)
        self.addChild(self.ball)
        self.addChild(self.racket)

    def start(self):
        self.addEventListener(Event.ENTER_FRAME, self.frame)
        self.racket.start()
        self.ball.start()
        self.old_frame = getTimer()

    def stop(self):
        self.ball.stop()
        self.racket.stop()
        self.removeEventListener(Event.ENTER_FRAME, self.frame)

    def frame(self, event):
        newframe = getTimer()
        delta = (newframe - self.old_frame)*0.001
        self.racket.frame(delta)
        self.ball.frame(delta)
        test = self.ball.hitTestObject
        if test(self.racket):
            self.ball.speed_y = -self.ball.speed_y
            if self.racket.speed:
                self.ball.speed_x += self.racket.speed*0.5
        bx = (self.ball.x - self.PADDING)
        bax = Math.floor((bx - self.BALLRADIUS) / self.BRICKWIDTH)
        bbx = Math.floor((bx + self.BALLRADIUS) / self.BRICKWIDTH)
        by = (self.ball.y - self.PADDING)
        bay = Math.floor((by - self.BALLRADIUS) / self.BRICKHEIGHT)
        bby = Math.floor((by + self.BALLRADIUS) / self.BRICKHEIGHT)
        self.label.text = [
                bax + ',' + bay,
                bax + ',' + bby,
                bbx + ',' + bay,
                bby + ',' + bby,
                ].join(', ')
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
        self.old_frame = newframe

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

    def draw(self):
        self.graphics.lineStyle(2)
        self.graphics.drawRoundRect(5, 5,
            self.TOTALWIDTH - 10, self.TOTALHEIGHT-10,
            self.ROUND, self.ROUND)

@package('arkanoid')
class Main(Sprite):
    def __init__(self):
        self.stage.align = StageAlign.TOP_LEFT
        self.stage.scaleMode = StageScaleMode.NO_SCALE
        f = Field(600, 400)
        self.addChild(f)
        f.start()
