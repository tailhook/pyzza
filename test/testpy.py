from flash.display import Sprite
from flash.text import TextField
from flash.text import TextFormat

class Hello:
    def __init__(self, value):
        self.value = 'Hello ' + value

@package('')
class Main(Sprite):

    def __init__(self):
        super().__init__()
        self.init('world')

    def init(self, value):
        label = TextField()
        label.background = True
        label.border = True
        label.defaultTextFormat = TextFormat('Courier New', 10)
        label.text = Hello(value).value
        self.addChild(label)
