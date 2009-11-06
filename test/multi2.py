from multi1 import Hello
from flash.display import Sprite
from flash.text import TextField

@package('multi2')
class HelloWorld(Hello):
    def __init__(self):
        super().__init__()
    def text(self):
        return super().text() + ' world!'


@package('main')
class Main(Sprite):
    def __init__(self):
        label = TextField()
        label.text = Hello().text() + '\n' + HelloWorld().text()
        self.addChild(label)
