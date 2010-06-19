from flash.display import Sprite
from flash.net import URLLoader, URLRequest
from flash.events import Event
from graph import Parser, Drawer

@package('graph')
class Main(Sprite):
    def __init__(self):
        params = self.loaderInfo.parameters
        request = URLRequest(params.url)
        self._loader = URLLoader()
        self._loader.dataFormat = 'text'
        self._loader.addEventListener(Event.COMPLETE, self.loaded)
        self._loader.load(request)

    def loaded(self, event):
        graph = Parser().parse(self._loader.data)
        Drawer(graph, self).draw()
