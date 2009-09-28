from flash.display import Sprite
from flash.text import TextField

class Main(Sprite):
    def __init__(self):
        label = TextField()
        trace(label.background)
        label.background = True
        label.border = True
        label.text = "Hello"
        self.addChild(label)
