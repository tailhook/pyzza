from flash.display import Sprite
from flash.display import StageAlign
from flash.display import StageScaleMode
from flash.events import KeyboardEvent
from flash.events import Event
from flash.text import TextField
from flash.utils import getTimer

class Ball(Sprite):
    def __init__(self, field):
        self.field = field
        self.graphics.beginFill(0xFF0000)
        self.graphics.drawCircle(0, 0, 10)
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
        self.y = field.TOTALHEIGHT - field.CUBEHEIGHT - field.PADDING
        self.graphics.beginFill(0x0000FF)
        self.graphics.drawRoundRect(0, 0, self.racket_width,
            field.CUBEHEIGHT, field.ROUND)
        self.graphics.endFill()
        self.graphics.beginFill(0xB0B0B0)
        self.graphics.drawRoundRect(field.LINEWIDTH, field.LINEWIDTH,
            self.racket_width - field.LINEWIDTH*2,
            field.CUBEHEIGHT - field.LINEWIDTH*2,
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
        #~ code = self.keycodes[ (event.altKey and 'a' or '')
                             #~ +(event.ctrlKey and 'c' or '')
                             #~ +(event.shiftKey and 's' or'')
                             #~ + String(event.keyCode)]
        code = self.keycodes[String(event.keyCode)]
        if code:
            self.keys[code] = True

    def keyup(self, event):
        #~ code = self.keycodes[ (event.altKey and 'a' or '')
                             #~ +(event.ctrlKey and 'c' or '')
                             #~ +(event.shiftKey and 's' or'')
                             #~ + String(event.keyCode)]
        code = self.keycodes[String(event.keyCode)]
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
    def __init__(self, field, left, top, width, height):
        self.x = field.PADDING + left*field.CUBEWIDTH + (left-1)*field.SPACING
        self.y = field.PADDING + top*field.CUBEHEIGHT + (top-1)*field.SPACING
        self.graphics.beginFill(0x808080)
        self.graphics.drawRoundRect(0, 0,
            width*field.CUBEWIDTH + field.SPACING*(width-1),
            height*field.CUBEHEIGHT + field.SPACING*(height-1),
            field.ROUND)
        self.graphics.endFill()
        self.graphics.beginFill(0xB0B0B0)
        self.graphics.drawRoundRect(field.LINEWIDTH, field.LINEWIDTH,
            width*field.CUBEWIDTH+field.SPACING*(width-1)-field.LINEWIDTH*2,
            height*field.CUBEHEIGHT+field.SPACING*(height-1)-field.LINEWIDTH*2,
            field.ROUND-field.LINEWIDTH)
        self.graphics.endFill()
        self.cacheAsBitmap = True

    def hit(self): # die on first hit
        return True

@package('arkanoid')
class Field(Sprite):
    def __init__(self, width, height):
        self.TOTALWIDTH = width
        self.TOTALHEIGHT = height
        self.init_const()
        self.draw()
        self.ball = Ball(self)
        self.racket = Racket(self)
        self.bricks = []
        self.make_bricks()
        self.addChild(self.ball)
        self.addChild(self.racket)
        for b in values(self.bricks):
            self.addChild(b)

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
        for b in values(self.bricks):
            if test(b) and b.hit():
                self.bricks.splice(self.bricks.indexOf(b), 1)
                self.removeChild(b)
        self.old_frame = newframe

    def init_const(self):
        self.PADDING = 20
        self.CUBEHEIGHT = 20
        self.CUBEWIDTH = 20
        self.SPACING = 10
        self.ROUND = 10
        self.LINEWIDTH = 3

    def draw(self):
        self.graphics.lineStyle(2)
        self.graphics.drawRoundRect(5, 5,
            self.TOTALWIDTH - 10, self.TOTALHEIGHT-10,
            self.ROUND, self.ROUND)

    def make_bricks(self):
        for i in range(5):
            self.make_line(i)

    def make_line(self, index):
        for j in range(10):
            self.bricks.push(Brick(self, j*3, index, 3, 1))

@package('arkanoid')
class Main(Sprite):
    def __init__(self):
        self.stage.align = StageAlign.TOP_LEFT
        self.stage.scaleMode = StageScaleMode.NO_SCALE
        f = Field(self.stage.stageWidth, self.stage.stageHeight)
        self.addChild(f)
        f.start()
