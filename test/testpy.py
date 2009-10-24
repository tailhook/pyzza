from flash.display import Sprite
from flash.text import TextField
from flash.text import TextFormat

class Hello:
    def __init__(self, value):
        self.text = "VAL: " + value + "\n"
        for i in range(value):
            self.text = self.text + "Hello!\n"
            if i > 3:
                self.text += "..."
                break
        else:
            self.text += "----"

@package('')
class Main(Sprite):

    def __init__(self):
        super().__init__()
        self.init('world')

    def init(self, value):
        label = TextField()
        label.background = True
        label.border = True
        label.text = Hello(Math.round(Math.random()*6)).text
        self.addChild(label)
