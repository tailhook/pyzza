
@package('graph')
class Base:
    __slots__ = (
        'style',
        'color',
        'fillcolor',
        'label',
        'fontcolor',
        )
    def __init__(self):
        pass

    def update_properties(self, data):
        for k, v in items(data):
            self[k] = v

@package('graph')
class Node(Base):
    __slots__ = (
        'name',
        'shape',
        'pos',
        'label_pos',
        'x',
        'y',
        'width',
        'height',
        )
    def __init__(self, name):
        super().__init__()
        self.name = name

    def update_properties(self, val):
        super().update_properties(val)
        if val.pos:
            self.parse_pos()
        if val.lp:
            self.parse_lp()

    def parse_pos(self):
        x, y = self.pos.split(',')
        self.x = float(x)
        self.y = float(y)

    def parse_lp(self):
        x, y = self.lp.split(',')
        self.label_pos = Point(float(x), float(y))

class Point:
    __slots__ = ['x', 'y']
    def __init__(self, x, y):
        self.x = x
        self.y = y

@package('graph')
class Edge(Base):
    __slots__ = (
        'pos', #actually path
        'lp', #label position
        'startnode',
        'endnode',
        'path',
        'startpoint',
        'endpoint',
        'arrowhead',
        'dir',
        )
    def __init__(self, snode, enode):
        self.startnode = snode
        self.endnode = enode

    def update_properties(self, val):
        super().update_properties(val)
        if val.pos:
            self.parse_pos()

    def parse_pos(self):
        arr = self.pos.split(' ')
        self.path = []
        self.startpoint = None
        self.endpoint = None
        for item in values(arr):
            if item.charAt(0) == 'e' or item.charAt(0) == 's':
                _c, x, y = item.split(',')
                pt = Point(float(x), float(y))
                if _c == 'e':
                    self.endpoint = pt
                else:
                    self.startpoint = pt
                continue
            x, y = item.split(',')
            self.path.push(Point(float(x), float(y)))

@package('graph')
class Subgraph(Base):
    __slots__ = (
        'bb', #bounding box
        'parent',
        'directed',
        'node_defaults',
        'edge_defaults',
        'nodes',
        'edges',
        'subgraphs',
        )
    def __init__(self, name, parent):
        super().__init__()
        self.name = name
        self.parent = parent
        self.node_defaults = {}
        self.edge_defaults = {}
        self.nodes = {}
        self.edges = []
        self.subgraphs = []
        self.directed = self.parent.directed
        self.update_node_defaults(self.parent.node_defaults)
        self.update_edge_defaults(self.parent.edge_defaults)

    def update_node_defaults(self, params):
        for k, v in items(params):
            self.node_params[k] = v

    def update_edge_defaults(self, params):
        for k, v in items(params):
            self.edge_params[k] = v

    def add_subgraph(self, name):
        gr = Subgraph(name, self)
        self.subgraphs.push(gr)
        return gr

    def add_edge(self, start, end, properties):
        edge = self.parent.add_edge(start, end, properties)
        self.edges.push(edge)
        return edge

    def add_node(self, name, properties):
        node = self.parent.add_node(name, properties)
        self.nodes[name] = node
        return node

@package('graph')
class AnonSubgraph(Subgraph):
    def __init__(self, parent):
        super().__init__(None, parent)

@package('graph')
class Graph(Base):
    __slots__ = (
        'name',
        'bb', #bounding box
        'rankdir',
        'size',
        'scalex',
        'scaley',
        'directed',
        'node_defaults',
        'edge_defaults',
        'nodes',
        'edges',
        'subgraphs',
        )
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.node_defaults = {
            'style': '',
            'color': 0x000000,
            'shape': 'ellipse',
            }
        self.edge_defaults = {
            'arrowhead': 'normal',
            'dir': 'forward',
            }
        self.nodes = {}
        self.edges = []
        self.subgraphs = []
        self.directed = False

    def update_properties(self, val):
        super().update_properties(val)
        if val.bb and self.size or val.size and self.bb:
            l,t,r,b = self.bb.split(',')
            w,h = self.size.split(',')
            self.scalex = r/w
            self.scaley = b/h

    def update_node_defaults(self, params):
        for k, v in items(params):
            self.node_defaults[k] = v

    def update_edge_defaults(self, params):
        for k, v in items(params):
            self.edge_defaults[k] = v

    def add_subgraph(self, name):
        gr = Subgraph(name, self)
        self.subgraphs.push(gr)
        return gr

    def add_anonsub(self):
        gr = AnonSubgraph(self)
        self.subgraphs.push(gr)
        return gr

    def add_edge(self, start, end, properties):
        snode = self.nodes[start]
        if not snode:
            snode = Node(start)
            self.nodes[start] = snode
        enode = self.nodes[end]
        if not enode:
            enode = Node(end)
            self.nodes[end] = enode
        edge = Edge(snode, enode)
        edge.update_properties(self.edge_defaults)
        edge.update_properties(properties)
        self.edges.push(edge)
        return edge

    def add_node(self, name, properties):
        node = self.nodes[name]
        if not node:
            node = Node(name)
            self.nodes[name] = node
        node.update_properties(self.node_defaults)
        node.update_properties(properties)
        return node

@package('graph')
class Digraph(Graph):
    __slots__ = []
    def __init__(self, name):
        super().__init__(name)
        self.directed = True
