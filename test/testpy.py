from flash.display import Sprite
from flash.text import TextField

@package('')
class Main(Sprite):
    def __init__(self):
        super().__init__()
        label = TextField()
        label.background = True
        label.border = True
        label.text = "Hello"
        self.addChild(label)
