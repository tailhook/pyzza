from flash.display import Sprite
from flash.text import TextField
from flash.text import TextFormat

@package('')
class Main(Sprite):

    def __init__(self):
        super().__init__()
        self.init()

    def init(self):
        label = TextField()
        label.background = True
        label.border = True
        label.defaultTextFormat = TextFormat('Courier New', 24)
        label.text = (2*3 + 4)/12
        self.addChild(label)
