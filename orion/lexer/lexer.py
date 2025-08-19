from .token import Token, TokenType, lookup_ident

class Lexer:
    def __init__(self, source_code: str):
        self.source = source_code
        self.position = 0  # current position in input (points to current char)
        self.read_position = 0  # current reading position in input (after current char)
        self.ch = ''  # current char under examination
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
        # Single line comment
        if self.peek_char() == '/':
            self.read_char() # consume '/'
            while self.ch != '\n' and self.ch != '':
                self.read_char()
            return True
        # Multi-line comment
        elif self.peek_char() == '*':
            self.read_char() # consume '*'
            self.read_char() # move to the character after '*'
            while not (self.ch == '*' and self.peek_char() == '/'):
                if self.ch == '': # EOF
                    # This is an unterminated comment, handle as an error
                    return False
                self.read_char()
            self.read_char() # consume '*'
            self.read_char() # consume '/'
            return True
        return False


    def next_token(self) -> Token:
        self.skip_whitespace()

        start_line = self.line
        start_col = self.column

        tok = None

        if self.ch == '=':
            if self.peek_char() == '=':
                self.read_char()
                tok = Token(TokenType.EQ, "==", start_line, start_col)
            else:
                tok = Token(TokenType.ASSIGN, self.ch, start_line, start_col)
        elif self.ch == ';':
            tok = Token(TokenType.SEMICOLON, self.ch, start_line, start_col)
        elif self.ch == ':':
            tok = Token(TokenType.COLON, self.ch, start_line, start_col)
        elif self.ch == '.':
            tok = Token(TokenType.DOT, self.ch, start_line, start_col)
        elif self.ch == '#':
            tok = Token(TokenType.HASH, self.ch, start_line, start_col)
        elif self.ch == '(':
            tok = Token(TokenType.LPAREN, self.ch, start_line, start_col)
        elif self.ch == ')':
            tok = Token(TokenType.RPAREN, self.ch, start_line, start_col)
        elif self.ch == ',':
            tok = Token(TokenType.COMMA, self.ch, start_line, start_col)
        elif self.ch == '+':
            tok = Token(TokenType.PLUS, self.ch, start_line, start_col)
        elif self.ch == '{':
            tok = Token(TokenType.LBRACE, self.ch, start_line, start_col)
        elif self.ch == '}':
            tok = Token(TokenType.RBRACE, self.ch, start_line, start_col)
        elif self.ch == '!':
            if self.peek_char() == '=':
                self.read_char()
                tok = Token(TokenType.NOT_EQ, "!=", start_line, start_col)
            else:
                tok = Token(TokenType.BANG, self.ch, start_line, start_col)
        elif self.ch == '-':
            tok = Token(TokenType.MINUS, self.ch, start_line, start_col)
        elif self.ch == '/':
            if self.peek_char() in ('/', '*'):
                self.skip_comment()
                return self.next_token()
            else:
                tok = Token(TokenType.SLASH, self.ch, start_line, start_col)
        elif self.ch == '*':
            tok = Token(TokenType.ASTERISK, self.ch, start_line, start_col)
        elif self.ch == '<':
            if self.peek_char() == '=':
                self.read_char()
                tok = Token(TokenType.LT_EQ, "<=", start_line, start_col)
            else:
                tok = Token(TokenType.LT, self.ch, start_line, start_col)
        elif self.ch == '>':
            if self.peek_char() == '=':
                self.read_char()
                tok = Token(TokenType.GT_EQ, ">=", start_line, start_col)
            else:
                tok = Token(TokenType.GT, self.ch, start_line, start_col)
        elif self.ch == '"':
            literal = self.read_string()
            tok = Token(TokenType.STRING, literal, start_line, start_col)
        elif self.ch == '':
            tok = Token(TokenType.EOF, "", self.line, self.column)
        else:
            if self.is_letter(self.ch):
                literal = self.read_identifier()
                token_type = lookup_ident(literal)
                return Token(token_type, literal, start_line, start_col)
            elif self.is_digit(self.ch):
                literal, is_float = self.read_number()
                token_type = TokenType.FLOAT if is_float else TokenType.INT
                return Token(token_type, literal, start_line, start_col)
            else:
                tok = Token(TokenType.ILLEGAL, self.ch, start_line, start_col)

        if tok is None:
             # This should not happen if all cases are handled
            tok = Token(TokenType.ILLEGAL, self.ch, start_line, start_col)

        self.read_char()
        return tok

    def read_identifier(self) -> str:
        start_pos = self.position
        while self.is_letter(self.ch) or self.is_digit(self.ch):
            self.read_char()
        return self.source[start_pos:self.position]

    def read_number(self) -> (str, bool):
        start_pos = self.position
        is_float = False
        while self.is_digit(self.ch):
            self.read_char()
        if self.ch == '.':
            is_float = True
            self.read_char()
            while self.is_digit(self.ch):
                self.read_char()
        return self.source[start_pos:self.position], is_float

    def read_string(self) -> str:
        self.read_char()  # Consume the opening "
        start_pos = self.position
        while self.ch != '"':
            if self.ch == '': # EOF
                # Unterminated string
                return ""
            self.read_char()
        end_pos = self.position
        # self.read_char() # Consume the closing "
        return self.source[start_pos:end_pos]

    def is_letter(self, char: str) -> bool:
        return 'a' <= char <= 'z' or 'A' <= char <= 'Z' or char == '_'

    def is_digit(self, char: str) -> bool:
        return '0' <= char <= '9'
