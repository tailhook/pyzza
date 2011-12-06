from logging import Console, Evaluator, Log
from flash.display import Sprite, StageAlign, StageScaleMode, Loader
from flash.net import URLRequest
from flash.events import Event
from flash.system import ApplicationDomain, SecurityDomain, LoaderContext
from string import repr
from flash.system import Security

@package('console')
class Main(Sprite):
    def __init__(self):
        Security.allowDomain('trypyzza.gafol.net')

        wurl = None
        newparams = {}
        for k, v in items(self.loaderInfo.parameters):
            if k == 'wrapped_url':
                wurl = v
            else:
                newparams[k] = v
        self.params = newparams
        if wurl:
            # wrapping an swf
            self.activate(self)
            Log.info("Loading url " + repr(wurl))
            self.load(wurl)
        elif not self.stage:
            # loaded using preloadswf
            self.addEventListener('allComplete', self._swf_loaded)
        else:
            # run standalone (can load internals yourself)
            self.activate(self)

    def _swf_loaded(self, event):
        self.activate(event.target.content)

    def activate(self, cont):
        cont.stage.align = StageAlign.TOP_LEFT
        cont.stage.scaleMode = StageScaleMode.NO_SCALE
        self.namespace = {
            'load': self.load,
            'params': self.params,
            'unload': self.unload,
            'root': cont,
            '_root': self,
            'print': self.print,
            'repr': repr,
            'locals': self.print_namespace,
            'stage': cont.stage,
            }
        self.console = Console(cont, Evaluator(self.namespace))
        self.namespace.console = self.console
        Log.add_handler(self.console)

    def load(self, url):
        if self.child:
            self.unload()
        context = LoaderContext()
        context.securityDomain = SecurityDomain.currentDomain
        context.applicationDomain = ApplicationDomain()
        context.checkPolicyFile = True
        req = URLRequest()
        req.url = url
        loader = Loader()
        for k, v in items(self.params):
            loader.contentLoaderInfo.parameters[k] = v
        self.addChild(loader)
        try:
            loader.load(req, context)
        except SecurityError as e:
            Log.error(str(e))
            Log.info("Trying different security domain, "
                "some functionality may be absent")
            Log.info("(It's ok if you are on local filesystem)")
            loader.load(req)
        self.child = loader
        loader.contentLoaderInfo.addEventListener(
            Event.COMPLETE, self._bindcontent)

    def _bindcontent(self, ev):
        self.removeChild(self.child)
        self.addChild(self.child.content)
        self.child = self.child.content
        if self.console.visible:
            self.setChildIndex(self.console, self.numChildren-1)

    def unload(self):
        if isinstance(self.child, Loader):
            self.child.contentLoaderInfo.removeEventListener(
                Event.COMPLETE, self._bindcontent)
        self.removeChild(self.child)
        self.child = None

    def get_root(self):
        return self.child

    def print(self, *values):
        values.__proto__ = Array.prototype
        self.console.add_text(values.join(' '))

    def print_namespace(self):
        for k, v in items(self.namespace):
            self.print("{0!s}: {1!r}".format(k, v))
