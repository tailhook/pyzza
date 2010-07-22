from string import repr
from flash.text import TextField
from flash.display import Sprite, StageAlign, StageScaleMode
from logging import Log, Console

class Holder:
    textbox = None
    def __init__(self):
        pass

@package('debuginfo')
class MyLog:

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
        self.stage.align = StageAlign.TOP_LEFT
        self.stage.scaleMode = StageScaleMode.NO_SCALE
        self.tf = TextField()
        Holder.textbox = self.tf
        self.addChild(self.tf)
        self.tf.width = 640
        self.tf.height = 480
        MyLog.warning("My Warning Function Called")
        Log.add_handler(Console(self))
        Log.info("Some info message")
        Log.warning("Some warning")
        Log.error("Some error message")
