from .token import Token, TokenType, lookup_ident

class Lexer:
    def __init__(self, source_code: str):
        self.source = source_code
        self.position = 0
        self.read_position = 0
        self.ch = ''
        self.line = 1
        self.column = 0
        self.read_char()

    def read_char(self):
        if self.read_position >= len(self.source):
            self.ch = ''  # EOF
        else:
            self.ch = self.source[self.read_position]

        if self.ch == '\n':
            self.line += 1
            self.column = 0
        else:
            self.column += 1

        self.position = self.read_position
        self.read_position += 1

    def peek_char(self) -> str:
        if self.read_position >= len(self.source):
            return ''
        return self.source[self.read_position]

    def skip_whitespace(self):
        while self.ch in [' ', '\t', '\n', '\r']:
            self.read_char()

    def skip_comment(self):
        if self.peek_char() == '/':
            self.read_char()
            while self.ch != '\n' and self.ch != '': self.read_char()
            return True
        elif self.peek_char() == '*':
            self.read_char()
            self.read_char()
            while not (self.ch == '*' and self.peek_char() == '/'):
                if self.ch == '': return False
                self.read_char()
            self.read_char(); self.read_char()
            return True
        return False

    def next_token(self) -> Token:
        self.skip_whitespace()
        start_line, start_col = self.line, self.column
        tok = None

        if self.ch == '=':
            if self.peek_char() == '=': self.read_char(); tok = Token(TokenType.EQ, "==", start_line, start_col)
            else: tok = Token(TokenType.ASSIGN, self.ch, start_line, start_col)
        elif self.ch == '+': tok = Token(TokenType.PLUS, self.ch, start_line, start_col)
        elif self.ch == '-': tok = Token(TokenType.MINUS, self.ch, start_line, start_col)
        elif self.ch == '!':
            if self.peek_char() == '=': self.read_char(); tok = Token(TokenType.NOT_EQ, "!=", start_line, start_col)
            else: tok = Token(TokenType.BANG, self.ch, start_line, start_col)
        elif self.ch == '/':
            if self.peek_char() in ('/', '*'): self.skip_comment(); return self.next_token()
            else: tok = Token(TokenType.SLASH, self.ch, start_line, start_col)
        elif self.ch == '*': tok = Token(TokenType.ASTERISK, self.ch, start_line, start_col)
        elif self.ch == '<':
            if self.peek_char() == '=': self.read_char(); tok = Token(TokenType.LT_EQ, "<=", start_line, start_col)
            else: tok = Token(TokenType.LT, self.ch, start_line, start_col)
        elif self.ch == '>':
            if self.peek_char() == '=': self.read_char(); tok = Token(TokenType.GT_EQ, ">=", start_line, start_col)
            else: tok = Token(TokenType.GT, self.ch, start_line, start_col)
        elif self.ch == ';': tok = Token(TokenType.SEMICOLON, self.ch, start_line, start_col)
        elif self.ch == ':': tok = Token(TokenType.COLON, self.ch, start_line, start_col)
        elif self.ch == ',': tok = Token(TokenType.COMMA, self.ch, start_line, start_col)
        elif self.ch == '.': tok = Token(TokenType.DOT, self.ch, start_line, start_col)
        elif self.ch == '#': tok = Token(TokenType.HASH, self.ch, start_line, start_col)
        elif self.ch == '(': tok = Token(TokenType.LPAREN, self.ch, start_line, start_col)
        elif self.ch == ')': tok = Token(TokenType.RPAREN, self.ch, start_line, start_col)
        elif self.ch == '{': tok = Token(TokenType.LBRACE, self.ch, start_line, start_col)
        elif self.ch == '}': tok = Token(TokenType.RBRACE, self.ch, start_line, start_col)
        elif self.ch == '[': tok = Token(TokenType.LBRACKET, self.ch, start_line, start_col)
        elif self.ch == ']': tok = Token(TokenType.RBRACKET, self.ch, start_line, start_col)
        elif self.ch == '"':
            literal = self.read_string()
            tok = Token(TokenType.STRING, literal, start_line, start_col)
        elif self.ch == '':
            tok = Token(TokenType.EOF, "", self.line, self.column)
        else:
            if self.is_letter(self.ch):
                literal = self.read_identifier()
                return Token(lookup_ident(literal), literal, start_line, start_col)
            elif self.is_digit(self.ch):
                literal, is_float = self.read_number()
                tok_type = TokenType.FLOAT if is_float else TokenType.INT
                return Token(tok_type, literal, start_line, start_col)
            else:
                tok = Token(TokenType.ILLEGAL, self.ch, start_line, start_col)

        self.read_char()
        return tok

    def read_identifier(self) -> str:
        start = self.position
        while self.is_letter(self.ch) or self.is_digit(self.ch): self.read_char()
        return self.source[start:self.position]

    def read_number(self) -> (str, bool):
        start = self.position
        is_float = False
        while self.is_digit(self.ch): self.read_char()
        if self.ch == '.':
            is_float = True
            self.read_char()
            while self.is_digit(self.ch): self.read_char()
        return self.source[start:self.position], is_float

    def read_string(self) -> str:
        self.read_char()
        start = self.position
        while self.ch != '"':
            if self.ch == '': return ""
            self.read_char()
        end = self.position
        return self.source[start:end]

    def is_letter(self, char: str) -> bool:
        return 'a' <= char <= 'z' or 'A' <= char <= 'Z' or char == '_'

    def is_digit(self, char: str) -> bool:
        return '0' <= char <= '9'
