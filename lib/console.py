
from flash.display import BitmapData, Sprite, Bitmap, PixelSnapping, Loader
from flash.events import Event, KeyboardEvent
from flash.text import TextField, TextFieldType, TextFormat
from flash.geom import Point, Rectangle
from flash.net import URLRequest

from logging import Log, LogLevel
from string import repr

class GlyphCache:
    def __init__(self):
        self.textformat = TextFormat("Consolas", 18, 0xDDDDDD)
        self.lineheight = 24
        self.textfield = TextField()
        self.textfield.setTextFormat(self.textformat)
        self.textfield.defaultTextFormat = self.textformat
        self.glyphs = {}
        self.colorcache = {}

    def draw_line(self, text, x, y, color, target, cursor=undefined):
        cbmp = self.colorcache[color]
        if not cbmp:
            cbmp = BitmapData(self.lineheight, self.lineheight, False, color)
            self.colorcache[color] = cbmp

        pt = Point(x, y)
        lines = 1

        for i in range(text.length):
            char = text.charCodeAt(i)
            if char == 10:
                pt.x = x
                pt.y += self.lineheight
                lines += 1
                continue
            glyph = self.glyphs[char]
            if not glyph:
                glyph = self._make_glyph(char)
                self.glyphs[char] = glyph
            target.copyPixels(cbmp, glyph.rect, pt, glyph, None, True)
            pt.x += glyph.rect.width - 1
            if cursor == i:
                target.copyPixels(cbmp, Rectangle(0, 0, 2, self.lineheight), pt)
        if cursor == text.length:
            target.copyPixels(cbmp, Rectangle(0, 0, 2, self.lineheight), pt)
        return lines

    def _make_glyph(self, code):
        self.textfield.text = String.fromCharCode(code)
        bmp = BitmapData(self.textfield.textWidth + 1, self.lineheight, True, 0x0)
        bmp.draw(self.textfield)
        return bmp

class Line:
    __slots__ = ['color', 'text']
    def __init__(self, color, text):
        self.color = color
        self.text = text

@package('logging.eval')
def evaluate(_):
    pass

@package('logging')
class Evaluator:

    def __init__(self, url="http://trypyzza.gafol.net/makeeval",
            ps1=">>> ", ps2="... "):
        self.url = url
        self.ps1 = ps1
        self.ps2 = ps2
        self.last_value = None
        self.scope = {'test': 22}

    def need_continue(self, input):
        return False

    def eval(self, console, input):
        val = ["""
from flash.display import Sprite
@package("logging.eval")
class Main(Sprite):
    def __init__(self):
        @__eval__
        def evaluate(_):
"""]
        first = True
        for i in values(input):
            val.push('            ' + i + '\n')
            if first:
                console.add_text(self.ps1 + i)
                first = False
            else:
                console.add_text(self.ps2 + i)
        val.push('        self.function = evaluate\n')
        data = val.join('')
        req = URLRequest()
        req.url = self.url
        req.method = 'POST'
        req.data = data
        cur = Loader()
        cur.load(req)

        def _run(ev):
            console.clearinput()
            fun = cur.content.function
            del self._cur
            try:
                self.last_value = fun.apply(self.scope, [self.last_value])
            except Error as e:
                console.add_text("Runtime Error: "+e.getStackTrace(),
                    console.levelcolors[LogLevel.ERROR])
            else:
                if self.last_value != undefined:
                    console.add_text(repr(self.last_value))

        cur.contentLoaderInfo.addEventListener(Event.COMPLETE, _run)

@package('logging')
class Console(Sprite):
    def __init__(self, canvas,
        evaluator=None,
        format="{1} at {file}:{line}: {2}"):
        self.levelcolors = {
            str(LogLevel.DEBUG): 0xC0C0C0,
            str(LogLevel.INFO): 0xC0C0C0,
            str(LogLevel.WARNING): 0xFFFFFF,
            str(LogLevel.ERROR): 0xFFC0C0,
            str(LogLevel.CRITICAL): 0xFFC0C0,
            }
        self.background_color = 0x000000
        self.input_color = 0xFFFFFF
        self.canvas = canvas
        self.evaluator = evaluator
        self.visible = False
        self.lines = []
        self.visible_lines = 0
        self.inputlines = ['']
        self.cursor = Point(0, 0)
        self.max_history = 100
        self.max_lines = 11000
        self.min_lines = 10000
        self.history = []
        self.firstvisible = -1
        self.history_index = 0
        self.cache = GlyphCache()
        self.format = format
        self.bmp = Bitmap(None, PixelSnapping.ALWAYS, False)
        self.addChild(self.bmp)
        canvas.stage.addEventListener(KeyboardEvent.KEY_DOWN, self.key)

    def log_record(self, rec):
        s = self.format.format(rec, LogLevel.name[rec.level], rec.format())
        self.add_text(s, self.levelcolors[rec.level])

    def add_text(self, text, color=0xFFFFFF):
        for rline in values(text.split('\n')):
            self.lines.push(Line(color, rline))
        if self.visible:
            if self.lines.length > self.max_lines:
                self.lines.splice(0, self.max_lines - self.min_lines)
            if self.firstvisible < 0 \
                or self.lines.length <= self.firstvisible+self.visible_lines:
                self.refresh()

    def clearinput(self):
        self.inputlines = [""]
        del self._storedlines
        self.cursor = Point(0, 0)
        self.resize()

    def key(self, event):
        if self.visible:
            if event.keyCode == 192: # tilde
                self.hide()
            elif event.keyCode == 13:
                if event.shiftKey or (self.evaluator \
                    and self.evaluator.need_continue(self.inputlines)):
                    self.inputlines.splice(self.cursor.y+1, 0, "")
                    self.cursor.y += 1
                    self.cursor.x = 0
                    self.resize()
                else:
                    code = self.inputlines.join('\n')
                    if self.evaluator:
                        self.evaluator.eval(self, self.inputlines)
                    else:
                        Log.info(code)
                    self.history.push(code)
                    self.history_index = -1
            elif event.keyCode == 33: # pageup
                oldline = self.firstvisible
                if oldline < 0:
                    self.firstvisible = max(0,
                        self.lines.length - self.visible_lines*3/2)
                else:
                    self.firstvisible = max(oldline - self.visible_lines/2, 0)
                if oldline != self.firstvisible:
                    self.refresh()
            elif event.keyCode == 34: # pagedown
                oldline = self.firstvisible
                if oldline < 0:
                    return
                self.firstvisible = oldline + self.visible_lines
                if self.firstvisible + self.visible_lines > self.lines.length:
                    self.firstvisible = -1
                if oldline != self.firstvisible:
                    self.refresh()
            elif event.keyCode == 37: # left
                if self.cursor.x == 0:
                    if self.inputlines.length > 1 and self.cursor.y:
                        self.cursor.y -= 1
                        self.cursor.x = self.inputlines[self.cursor.y].length
                else:
                    self.cursor.x -= 1
                self.refreshinput()
            elif event.keyCode == 39: # right
                if self.cursor.x == self.inputlines[self.cursor.y]:
                    if self.inputlines.length > self.cursor.y:
                        self.cursor.y += 1
                        self.cursor.x = 0
                else:
                    self.cursor.x += 1
                self.refreshinput()
            elif event.keyCode == 38: # up
                if event.shiftKey:
                    self.cursor.y = max(self.cursor.y-1, 0)
                else:
                    if self.history_index < 0:
                        self._storedlines = self.inputlines
                        self.history_index = self.history.length
                    if self.history_index > 0:
                        self.inputlines = self.history[self.history_index-1]\
                            .split('\n')
                        self.cursor = Point(
                            self.inputlines[self.inputlines.length-1].length,
                            self.inputlines.length-1)
                        self.history_index -= 1
                self.refreshinput()
            elif event.keyCode == 40: # down
                if event.shiftKey:
                    self.cursor.y = min(self.cursor.y+1,
                        self.inputlines.length-1)
                else:
                    if self.history_index+1 < self.history.length:
                        self.inputlines = self.history[self.history_index+1]\
                            .split('\n')
                        self.history_index += 1
                    elif self._storedlines:
                        self.inputlines = self._storedlines
                        self.history_index = -1
                        del self._stored_lines
                    self.cursor = Point(
                        self.inputlines[self.inputlines.length-1].length,
                        self.inputlines.length-1)
                self.refreshinput()
            elif event.keyCode == 0x08: #backspace
                if self.cursor.x:
                    ln = self.inputlines[self.cursor.y]
                    if self.cursor.x == ln.length:
                        nln = ln.substr(0, ln.length-1)
                    else:
                        nln = ln.substr(0, self.cursor.x-1)+ln.substr(self.cursor.x)
                    self.inputlines[self.cursor.y] = nln
                    self.cursor.x -= 1
                    self.refreshinput()
                elif self.cursor.y:
                    self.cursor.y -= 1
                    prevline = self.inputlines[self.cursor.y-1]
                    self.cursor.x = prevline.length
                    self.inputlines[self.cursor.y-1] \
                        = prevline + self.inputlines[self.cursor.y]
                    self.resize()
            elif event.charCode >= 0x20: # all chars starting from space
                ln = self.inputlines[self.cursor.y]
                ch = String.fromCharCode(event.charCode)
                if self.cursor.x == ln.length:
                    nln = ln+ch
                else:
                    nln = ln.substr(0,self.cursor.x)+ch+ln.substr(self.cursor.x)
                self.inputlines[self.cursor.y] = nln
                self.cursor.x += 1
                self.refreshinput()
        else:
            if event.keyCode == 192: # tilde
                self.show()

    def show(self):
        self.visible = True
        self.canvas.addChild(self)
        self.stage.addEventListener(Event.RESIZE, self.resize)
        self.resize()

    def hide(self):
        self.visible = False
        self.bmp.bitmapData.dispose()
        self.stage.removeEventListener(Event.RESIZE, self.resize)
        self.canvas.removeChild(self)

    def resize(self, ev=None):
        self.visible_lines = int(self.stage.stageHeight
            / self.cache.lineheight * 2/3)-self.inputlines.length
        self.mybitmap = BitmapData(self.stage.stageWidth,
            self.cache.lineheight*(self.visible_lines+self.inputlines.length)+4,
            False, 0x000000)
        self.bmp.bitmapData = self.mybitmap
        self.refresh()

    def refresh(self):
        self.mybitmap.fillRect(self.mybitmap.rect, self.background_color)
        if self.lines.length < self.visible_lines:
            for i in range(self.lines.length):
                line = self.lines[i]
                self.cache.draw_line(line.text, 2, i*self.cache.lineheight+2,
                    line.color, self.mybitmap)
        else:
            if self.firstvisible < 0:
                start = self.lines.length - self.visible_lines
            else:
                start = self.firstvisible
            for i in range(self.visible_lines):
                line = self.lines[start + i]
                self.cache.draw_line(line.text, 2, i*self.cache.lineheight+2,
                    line.color, self.mybitmap)
        self.refreshinput()

    def refreshinput(self):
        self.mybitmap.fillRect(Rectangle(0, self.cache.lineheight*self.visible_lines,
            self.stage.stageWidth, self.inputlines.length*self.cache.lineheight+2), self.background_color)
        for i in range(self.inputlines.length):
            line = self.inputlines[i]
            self.cache.draw_line(line, 2,
                (self.visible_lines+i)*self.cache.lineheight+2,
                self.input_color, self.mybitmap,
                self.cursor.x if self.cursor.y == i else undefined)
