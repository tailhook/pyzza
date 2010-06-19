from flash.text.engine import (TextElement, ElementFormat, FontDescription,
    TextBlock)
from graph import Colors

@package('graph')
class Drawer:
    def __init__(self, graph, sprite):
        self.graph = graph
        self.sprite = sprite
        self.canvas = sprite.graphics

    def color(self, value):
        if not value:
            return 0
        if value.charAt(0) == '#':
            return int('0x' + value.substring(1))
        else:
            return Colors.x11[value.toLowerCase()]

    def draw(self):
        for node in values(self.graph.nodes):
            self['node_' + node.shape](node)
            self.label_node(node)
        for edge in values(self.graph.edges):
            self.draw_edge(edge)

    def node_ellipse(self, node):
        if node.style == 'filled':
            self.canvas.beginFill(self.color(node.color))
        else:
            self.canvas.lineStyle(1, self.color(node.color))
        self.canvas.drawEllipse(node.x-node.width*36, node.y-node.height*36,
            node.width*72, node.height*72)
        if node.style == 'filled':
            self.canvas.endFill()

    def node_circle(self, node):
        if node.style == 'filled':
            self.canvas.beginFill(self.color(node.fillcolor))
        else:
            self.canvas.lineStyle(1, self.color(node.color))
        self.canvas.drawCircle(node.x, node.y, node.width*36)
        if node.style == 'filled':
            self.canvas.endFill()

    def node_doublecircle(self, node):
        self.canvas.lineStyle(1, self.color(node.color))
        self.canvas.drawCircle(node.x, node.y, node.width*36)
        if node.style == 'filled':
            self.canvas.beginFill(self.color(node.fillcolor))
        self.canvas.drawCircle(node.x, node.y, node.width*36 - 4)
        if node.style == 'filled':
            self.canvas.endFill()

    def draw_edge(self, edge):
        self.canvas.lineStyle(1, self.color(edge.color))
        if self.startpoint:
            self.canvas.moveTo(edge.startpoint.x, edge.startpoint.y)
            self.canvas.lineTo(edge.path[0].x, edge.path[0].y)
        else:
            self.canvas.moveTo(edge.path[0].x, edge.path[0].y)
        for i in range(1, edge.path.length, 3):
            self.canvas.curveTo(edge.path[i].x, edge.path[i].y,
                (edge.path[i].x+edge.path[i+1].x)*0.5,
                (edge.path[i].y+edge.path[i+1].y)*0.5)
            self.canvas.curveTo(edge.path[i+1].x, edge.path[i+1].y,
                edge.path[i+2].x, edge.path[i+2].y)
        self['arrow_' + edge.arrowhead](self.color(edge.color),
            edge.path[edge.path.length-1], edge.endpoint)

    def arrow_normal(self, color, center, end):
        dx =  center.x - end.x
        dy =  center.y - end.y
        s = 0.259 # sin 15
        c = 0.966 # cos 15
        ax = (dx*c - dy*s)*1.5
        ay = (dx*s + dy*c)*1.5
        s = -0.259 # sin -15
        c = 0.966 # cos -15
        bx = (dx*c - dy*s)*1.5
        by = (dx*s + dy*c)*1.5
        self.canvas.beginFill(color)
        self.canvas.moveTo(end.x, end.y)
        self.canvas.lineTo(end.x+ax, end.y+ay)
        self.canvas.lineTo(center.x, center.y)
        self.canvas.lineTo(end.x+bx, end.y+by)
        self.canvas.endFill()

    def label_node(self, node):
        font = FontDescription("Arial")
        format = ElementFormat(font)
        format.fontSize = 14
        el = TextElement(node.label or node.name, format)
        block = TextBlock()
        block.content = el
        tl = block.createTextLine(None, node.width*36)
        pos = node.label_pos
        if not pos:
            pos = node
        tl.x = int(pos.x-tl.width/2)
        tl.y = int(pos.y+tl.height/2)
        self.sprite.addChild(tl)
