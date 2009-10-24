from flash.display import Sprite
from flash.text import TextField
from flash.text import TextFormat

class Hello:
    def __init__(self):
        if Math.random() > 0.5:
            self.text = "Hello"
        else:
            self.text = "Shit"

@package('')
class Main(Sprite):

    def __init__(self):
        super().__init__()
        self.init('world')

    def init(self, value):
        label = TextField()
        label.background = True
        label.border = True
        label.text = Hello().text
        self.addChild(label)
