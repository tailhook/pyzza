from string import repr
from graph import Graph, Digraph

class Token:
    __slots__ = []
    def __init__(self): pass
class TokenEnd(Token):
    __slots__ = []
    def __init__(self): pass

class TokenName(Token):
    __slots__ = ['value']
    def __init__(self, value): self.value = value
class TokenString(Token):
    __slots__ = ['value']
    def __init__(self, value): self.value = value

class TokenSpace(Token):
    __slots__ = []
    def __init__(self): pass
class TokenComment(Token):
    __slots__ = []
    def __init__(self): pass

class TokenLbrace(Token):
    __slots__ = []
    def __init__(self): pass
class TokenRbrace(Token):
    __slots__ = []
    def __init__(self): pass
class TokenLbracket(Token):
    __slots__ = []
    def __init__(self): pass
class TokenRbracket(Token):
    __slots__ = []
    def __init__(self): pass

class TokenEq(Token):
    __slots__ = []
    def __init__(self): pass
class TokenSemicolon(Token):
    __slots__ = []
    def __init__(self): pass
class TokenComma(Token):
    __slots__ = []
    def __init__(self): pass

class TokenEdge(Token):
    __slots__ = []
    def __init__(self): pass
class TokenDiedge(Token):
    __slots__ = []
    def __init__(self): pass

token_chars = {
    '{': TokenLbrace,
    '}': TokenRbrace,
    '[': TokenLbracket,
    ']': TokenRbracket,
    '=': TokenEq,
    ';': TokenSemicolon,
    ',': TokenComma,
    '-': TokenEdge,
    '"': TokenString,
    '#': TokenComment,
    ' ': TokenSpace,
    '\r': TokenSpace,
    '\n': TokenSpace,
    '	': TokenSpace,
    }
alnum = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789'
for i in range(alnum.length):
    token_chars[alnum.charAt(i)] = TokenName
escapes = {
    'n': '\n',
    'N': '', # probably means nothing
    'r': '\r',
    '\\': '\\',
    '"': '"',
    '\n': '',
    '\r': '',
    }

@package('graph')
class SyntaxError(Error):
    __slots__ = []
    def __init__(self, message):
        super().__init__(message)

class Tokenizer:
    def __init__(self, string):
        self.data = string
        self.index = 0
        self.line = 1
        self.line_start = 0
        self.token = None

    def peek(self):
        if self.token == None:
            self.token = self._next()
        return self.token

    def next(self):
        if self.token != None:
            res = self.token
            self.token = None
            return res
        return self._next()

    def _next(self):
        data = self.data
        if self.index >= data.length:
            return TokenEnd()
        ch = data.charAt(self.index)
        self.index += 1
        tt = token_chars[ch]
        if tt == TokenSpace:
            while self.index < data.length:
                if ch == '\n':
                    self.line += 1
                    self.line_start = self.index
                ch = data.charAt(self.index)
                if token_chars[ch] != TokenSpace:
                    break
                self.index += 1
            else:
                return TokenEnd()
            return self.next() # skipping name
        elif tt == TokenName:
            start = self.index - 1
            while self.index < data.length:
                if token_chars[data.charAt(self.index)] != TokenName:
                    break
                self.index += 1
            end = self.index
            return TokenName(data.substring(start, end))
        elif tt == TokenString:
            res = ""
            while self.index < data.length:
                ch1 = data.charAt(self.index)
                self.index += 1
                if ch1 == '\\':
                    if self.index >= data.length:
                        self.syntax_error()
                    res += escapes[data.charAt(self.index)]
                    self.index += 1
                elif ch1 == ch:
                    return TokenString(res)
                elif ch1 == '\r' or ch1 == '\n':
                    raise self.syntax_error()
                else:
                    res += ch1
            else:
                self.syntax_error()
        elif tt == TokenComment:
            while self.index < data.length:
                ch = data.charAt(self.index)
                if ch == '\n' or ch == '\r':
                    break
                self.index += 1
            else:
                return TokenEnd()
            return self.next() # skipping name
        elif tt == TokenEdge:
            if self.index >= data.length:
                self.syntax_error("Unexpected EOF")
            tok = None
            ch = data.charAt(self.index)
            if ch == '-':
                tok = TokenEdge()
            elif ch == '>':
                tok = TokenDiedge()
            else:
                self.syntax_error()
            self.index += 1
            return tok
        else:
            if tt:
                return (Class(tt))()
            else:
                self.syntax_error("Wrong char {0!r} (0x{1:02x})"
                    .format(ch, float(ch.charCodeAt(0))))

    def syntax_error(self, message="SyntaxError"):
        # TODO: show line number and position
        raise SyntaxError(message + ' at line {0:d} char {1:d}'
            .format(self.line, self.index - self.line_start))


@package('graph')
class Parser:

    ############
    # Grammar:
    #   graph: type NAME '{' graphbody '}'
    #   type: 'digraph' | 'graph'
    #   graphbody: entity*
    #   entity: prototype | node | edge | subgraph | anonsubgraph;
    #   prototype: 'graph' params ';' | 'node' params ';' | 'edge' params ';'
    #   node: NAME params? ';'
    #   edge: NAME '--' NAME params? ';'
    #   subgraph: 'subgraph' NAME '{' graphbody '}'
    #   anonsubgraph: '{' graphbody '}'
    ############

    def __init__(self):
        pass

    def parse(self, data):
        self.tokenizer = Tokenizer(data.replace('\r\n', '\n'))
        return self.parse_graph()

    # parser state functions
    def parse_graph(self):
        tok = self.get_token(TokenName)
        name = self.get_token(TokenName)
        if tok.value == 'graph':
            res = Graph(name.value)
        elif tok.value == 'digraph':
            res = Digraph(name.value)
        else:
            self.syntax_error('Wrong graph declaration')
        lbrace = self.get_token(TokenLbrace)
        self.parse_graphbody(res)
        rbrace = self.get_token(TokenRbrace)
        self.get_token(TokenEnd)
        return res

    def parse_graphbody(self, graph):
        tok = self.tokenizer.peek()
        while not isinstance(tok,TokenRbrace):
            if isinstance(tok, TokenName) or isinstance(tok, TokenString):
                if tok.value == 'graph':
                    self.parse_graphparams(graph)
                elif tok.value == 'node':
                    self.parse_nodedefaults(graph)
                elif tok.value == 'edge':
                    self.parse_edgedefaults(graph)
                elif tok.value == 'subgraph':
                    self.parse_subgraph(graph)
                else:
                    # node or edge
                    name = self.tokenizer.next()
                    nex = self.tokenizer.peek()
                    if isinstance(nex, TokenEdge) or isinstance(nex,TokenDiedge):
                        self.parse_edge(graph, name)
                    else:
                        self.parse_node(graph, name)
            elif isinstance(tok, TokenLbrace):
                self.parse_anonsub(graph)
            else:
                self.syntax_error(tok, [TokenName, TokenString,
                    TokenLbrace, TokenRbrace])
            tok = self.tokenizer.peek()

    def parse_graphparams(self, graph):
        tok = self.get_token(TokenName)
        val = self.parse_params()
        self.get_token(TokenSemicolon)
        graph.update_properties(val)

    def parse_nodedefaults(self, graph):
        tok = self.get_token(TokenName)
        val = self.parse_params()
        self.get_token(TokenSemicolon)
        graph.update_node_defaults(val)

    def parse_edgedefaults(self, graph):
        tok = self.get_token(TokenName)
        val = self.parse_params()
        self.get_token(TokenSemicolon)
        graph.update_edge_defaults(val)

    def parse_subgraph(self, graph):
        tok = self.get_token(TokenName)
        name = self.get_token(TokenName)
        sub = graph.add_subgraph(name.value)
        self.get_token(TokenLbrace)
        self.parse_graphbody(sub)
        self.get_token(TokenRbrace)

    def parse_anonsub(self, graph):
        sub = graph.add_anonsub()
        self.get_token(TokenLbrace)
        self.parse_graphbody(sub)
        self.get_token(TokenRbrace)

    def parse_edge(self, graph, start):
        tok = self.tokenizer.next()
        if isinstance(tok, TokenEdge):
            if graph.directed:
                self.syntax_error(tok, [TokenDiedge])
        elif isinstance(tok, TokenDiedge):
            if not graph.directed:
                self.syntax_error(tok, [TokenEdge])
        else:
            self.syntax_error()
        end = self.get_string()
        if isinstance(self.tokenizer.peek(), TokenLbracket):
            val = self.parse_params()
        else:
            val = {}
        self.get_token(TokenSemicolon)
        graph.add_edge(start.value, end.value, val)

    def parse_node(self, graph, name):
        if isinstance(self.tokenizer.peek(), TokenLbracket):
            val = self.parse_params()
        else:
            val = {}
        self.get_token(TokenSemicolon)
        graph.add_node(name.value, val)

    def parse_params(self):
        self.get_token(TokenLbracket)
        tok = self.tokenizer.next()
        if isinstance(tok, TokenRbracket):
            return {}
        name = tok
        eq = self.get_token(TokenEq)
        value = self.get_string()
        res = {str(name.value): value.value}
        while True:
            tok = self.tokenizer.next()
            if isinstance(tok, TokenRbracket):
                break
            elif isinstance(tok, TokenComma):
                pass
            else:
                self.syntax_error(tok, [TokenRbracket, TokenComma])
            name = self.get_token(TokenName)
            eq = self.get_token(TokenEq)
            value = self.get_string()
            res[str(name.value)] = value.value
        return res

    # Utility functions
    def get_token(self, type):
        tok = self.tokenizer.next()
        if not isinstance(tok, type):
            self.syntax_error(tok, [type])
        return tok

    def get_string(self):
        tok = self.tokenizer.next()
        if isinstance(tok, TokenString) or isinstance(tok, TokenName):
            return tok
        self.syntax_error(tok, [TokenString, TokenComma])

    def syntax_error(self, has, expected):
        # TODO: show line number, position and expected tokens
        raise SyntaxError('Unexpected token {0!r}, need one of {1} '
            'at line {2:d} char {3:d}'.format(has, expected,
            self.tokenizer.line, self.tokenizer.index -\
            self.tokenizer.line_start))
