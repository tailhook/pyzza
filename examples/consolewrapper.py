from logging import Console, Evaluator, Log
from flash.display import Sprite, StageAlign, StageScaleMode, Loader
from flash.net import URLRequest
from flash.events import Event
from flash.system import ApplicationDomain, SecurityDomain, LoaderContext
from string import repr

@package('console')
class Main(Sprite):
    def __init__(self):
        self.stage.align = StageAlign.TOP_LEFT
        self.stage.scaleMode = StageScaleMode.NO_SCALE
        wurl = None
        newparams = {}
        for k, v in items(self.loaderInfo.parameters):
            if k == 'wrapped_url':
                wurl = v
            else:
                newparams[k] = v
        self.params = newparams
        self.namespace = {
            'load': self.load,
            'params': newparams,
            'unload': self.unload,
            'root': self.get_root,
            '_root': self,
            'print': self.print,
            'repr': repr,
            'locals': self.print_namespace,
            }
        self.console = Console(self, Evaluator(self.namespace))
        self.namespace.console = self.console
        Log.add_handler(self.console)
        if wurl:
            Log.info("Loading url " + repr(wurl))
            self.load(wurl)

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
        loader.addEventListener(Event.COMPLETE, self._bindcontent)

    def _bindcontent(self):
        Log.info('done')
        self.removeChild(self.child)
        self.addChild(self.child.content)
        self.child = self.child.content

    def unload(self):
        if isinstance(self.child, Loader):
            self.child.removeEventListener(Event.COMPLETE, self._bindcontent)
        self.removeChild(self.child)
        self.child = None

    def get_root(self):
        return self.child

    def print(self, text):
        self.console.add_text(text)

    def print_namespace(self):
        for k, v in items(self.namespace):
            self.print("{0!s}: {1!r}".format(k, v))
