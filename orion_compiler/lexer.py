from typing import List, Any

from tokens import Token, TokenType, keywords


class Lexer:
    """
    The Lexer class, also known as a scanner or tokenizer.
    It takes the source code as a string and breaks it into a list of tokens.
    """
    def __init__(self, source: str):
        self.source: str = source
        self.tokens: List[Token] = []
        self.start: int = 0
        self.current: int = 0
        self.line: int = 1

    def scan_tokens(self) -> List[Token]:
        """Scans the entire source code and returns a list of tokens."""
        while not self._is_at_end():
            self.start = self.current
            self._scan_token()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def _advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        return char

    def _add_token(self, token_type: TokenType, literal: Any = None):
        text = self.source[self.start:self.current]
        self.tokens.append(Token(token_type, text, literal, self.line))

    def _match(self, expected: str) -> bool:
        if self._is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        self.current += 1
        return True

    def _peek(self) -> str:
        if self._is_at_end():
            return '\0'
        return self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def _string(self, quote_char: str):
        while self._peek() != quote_char and not self._is_at_end():
            if self._peek() == '\n':
                self.line += 1
            self._advance()

        if self._is_at_end():
            # Handle unterminated string error
            print(f"[Line {self.line}] Error: Unterminated string.")
            return

        self._advance()  # The closing quote.

        # Trim the surrounding quotes.
        value = self.source[self.start + 1:self.current - 1]
        self._add_token(TokenType.STRING, value)

    def _number(self):
        while self._is_digit(self._peek()):
            self._advance()

        # Look for a fractional part.
        if self._peek() == '.' and self._is_digit(self._peek_next()):
            # Consume the "."
            self._advance()

            while self._is_digit(self._peek()):
                self._advance()

        value = float(self.source[self.start:self.current])
        # Store as int if it has no fractional part
        if value == int(value):
            value = int(value)

        self._add_token(TokenType.NUMBER, value)

    def _identifier(self):
        while self._is_alpha_numeric(self._peek()):
            self._advance()

        text = self.source[self.start:self.current]
        token_type = keywords.get(text, TokenType.IDENTIFIER)
        self._add_token(token_type)

    def _block_comment(self):
        while not (self._peek() == '*' and self._peek_next() == '/') and not self._is_at_end():
            if self._peek() == '\n':
                self.line += 1
            self._advance()

        if self._is_at_end():
            print(f"[Line {self.line}] Error: Unterminated block comment.")
            return

        # Consume the closing */
        self._advance()
        self._advance()

    def _scan_token(self):
        char = self._advance()

        # Single-character tokens
        if char == '(': self._add_token(TokenType.LEFT_PAREN)
        elif char == ')': self._add_token(TokenType.RIGHT_PAREN)
        elif char == '{': self._add_token(TokenType.LEFT_BRACE)
        elif char == '}': self._add_token(TokenType.RIGHT_BRACE)
        elif char == ',': self._add_token(TokenType.COMMA)
        elif char == '.': self._add_token(TokenType.DOT)
        elif char == '-': self._add_token(TokenType.MINUS)
        elif char == '+': self._add_token(TokenType.PLUS)
        elif char == ';': self._add_token(TokenType.SEMICOLON)
        elif char == '*': self._add_token(TokenType.STAR)
        elif char == ':': self._add_token(TokenType.COLON)
        elif char == '#': self._add_token(TokenType.HASH)

        # One or two character tokens
        elif char == '!': self._add_token(TokenType.BANG_EQUAL if self._match('=') else TokenType.BANG)
        elif char == '=':
            if self._match('='): self._add_token(TokenType.EQUAL_EQUAL)
            elif self._match('>'): self._add_token(TokenType.ARROW)
            else: self._add_token(TokenType.EQUAL)
        elif char == '<': self._add_token(TokenType.LESS_EQUAL if self._match('=') else TokenType.LESS)
        elif char == '>': self._add_token(TokenType.GREATER_EQUAL if self._match('=') else TokenType.GREATER)

        # Comments
        elif char == '/':
            if self._match('/'):
                # A comment goes until the end of the line.
                while self._peek() != '\n' and not self._is_at_end():
                    self._advance()
            elif self._match('*'):
                self._block_comment()
            else:
                self._add_token(TokenType.SLASH)

        # Whitespace
        elif char in [' ', '\r', '\t']:
            pass
        elif char == '\n':
            self.line += 1

        # Literals
        elif char == '"': self._string('"')
        elif char == "'": self._string("'")
        elif self._is_digit(char): self._number()
        elif self._is_alpha(char): self._identifier()

        else:
            print(f"[Line {self.line}] Error: Unexpected character: {char}")

    # Helper methods
    def _is_digit(self, char: str) -> bool:
        return '0' <= char <= '9'

    def _is_alpha(self, char: str) -> bool:
        return ('a' <= char <= 'z') or ('A' <= char <= 'Z') or char == '_'

    def _is_alpha_numeric(self, char: str) -> bool:
        return self._is_alpha(char) or self._is_digit(char)
