from flash.events import Event, KeyboardEvent
from flash.utils import getTimer
from flash.text import TextField

@package('game')
class Keys:
    stage = None
    keys = None
    keycodes = None
    LEFT = '37'
    UP = '38'
    RIGHT = '39'
    DOWN = '40'
    F1 = '112'
    F2 = '113'
    F3 = '114'
    F4 = '115'
    F5 = '116'
    F6 = '117'
    F7 = '118'
    F8 = '119'
    F9 = '120'
    F10 = '121'
    F11 = '122'
    F12 = '123'

    def __init__(self):
        raise Error("This class only contains static properties and methods")

    @classmethod
    def start(self, stage):
        stage.addEventListener(KeyboardEvent.KEY_DOWN, self.keydown)
        stage.addEventListener(KeyboardEvent.KEY_UP, self.keyup)
        self.stage = stage
        self.keys = {}
        self.keycodes = {}

    @classmethod
    def stop(self):
        self.stage.removeEventListener(KeyboardEvent.KEY_DOWN, self.keydown)
        self.stage.removeEventListener(KeyboardEvent.KEY_UP, self.keyup)
        self.keys = None
        self.stage = None

    @classmethod
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

    @classmethod
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

    @classmethod
    def register(self, key, name):
        self.keycodes[key] = name

    @classmethod
    def unregister(self, key):
        del self.keycodes[key]

@package('game')
class Frame:
    sprite = None
    lastframe = None
    handlers = None
    show_fps = False
    fps = None

    def __init__(self):
        raise Error("This class only contains static properties and methods")

    @classmethod
    def start(self, sprite, show_fps=False):
        self.sprite = sprite
        self.lastframe = getTimer()
        self.handlers = []
        sprite.addEventListener(Event.ENTER_FRAME, self.frame)
        self.show_fps = show_fps
        if show_fps:
            self.fps = TextField()
            sprite.addChild(self.fps)

    @classmethod
    def stop(self):
        if self.fps:
            self.spite.delChild(self.fps)
        self.sprite.removeEventListener(Event.ENTER_FRAME, self.frame)
        self.sprite = None

    @classmethod
    def frame(self, ev):
        nt = getTimer()
        delta = (nt - self.lastframe)*0.001
        for fun in values(self.handlers):
            fun(delta)
        self.lastframe = nt
        if self.show_fps:
            self.fps.text = 'fps: ' + (1/delta).toFixed(2)

    @classmethod
    def attach(self,  handler):
        self.handlers.push(handler)

    @classmethod
    def detach(self, handler):
        self.handlers.splice(self.handlers.indexOf(handler), 1)
