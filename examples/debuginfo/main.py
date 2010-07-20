from string import repr
from flash.text import TextField
from flash.display import Sprite

class Holder:
    textbox = None
    def __init__(self):
        pass

@package('debuginfo')
class Log:

    def __init__(self):
        pass

    @staticmethod
    @debuginfo("file", "line", "class", "method")
    @debuglevel("WARNING")
    def warning(file, line, class_, method, message):
        Holder.textbox.appendText("WARNING:{0}:{1}:{2}:{3}: {4}".format(
            file.substr(file.lastIndexOf('/')+1), line, class_, method, message))

@package('debuginfo')
class Main(Sprite):
    def __init__(self):
        self.tf = TextField()
        Holder.textbox = self.tf
        self.addChild(self.tf)
        self.tf.width = 640
        self.tf.height = 480
        Log.warning("hello")
