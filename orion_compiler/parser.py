from typing import List, Optional

from tokens import Token, TokenType
import ast_nodes as ast


class ParseError(RuntimeError):
    """A custom exception for reporting syntax errors."""
    pass


class Parser:
    """
    The Parser consumes a stream of tokens and produces an Abstract Syntax Tree (AST).
    """
    def __init__(self, tokens: List[Token]):
        self.tokens: List[Token] = tokens
        self.current: int = 0

    def parse(self) -> List[ast.Stmt]:
        """The main entry point, parses a list of statements."""
        statements: List[ast.Stmt] = []
        while not self._is_at_end():
            declaration = self._declaration()
            if declaration is not None:
                statements.append(declaration)
        return statements

    # --- GRAMMAR RULE IMPLEMENTATIONS ---

    def _declaration(self) -> Optional[ast.Stmt]:
        """
        Parses a declaration. This is the main entry point for statements.
        If a syntax error is found, it synchronizes and returns None.
        """
        try:
            if self._match(TokenType.VAR):
                return self._var_declaration()
            return self._statement()
        except ParseError:
            self._synchronize()
            return None

    def _var_declaration(self) -> ast.Stmt:
        """Parses a variable declaration: 'var' IDENTIFIER ('=' expression)? ';'"""
        name = self._consume(TokenType.IDENTIFIER, "Expect variable name.")

        initializer: Optional[ast.Expr] = None
        if self._match(TokenType.EQUAL):
            initializer = self._expression()

        self._consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return ast.Var(name, initializer)

    def _statement(self) -> ast.Stmt:
        """Parses a statement. For now, only expression statements are supported."""
        return self._expression_statement()

    def _expression_statement(self) -> ast.Stmt:
        """Parses an expression statement: expression ';'"""
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return ast.Expression(expr)

    def _expression(self) -> ast.Expr:
        """Parses an expression. Entry point for all expression rules."""
        return self._equality()

    def _equality(self) -> ast.Expr:
        """Parses an equality expression (==)."""
        expr = self._comparison()
        while self._match(TokenType.EQUAL_EQUAL):
            operator = self._previous()
            right = self._comparison()
            expr = ast.Binary(expr, operator, right)
        return expr

    def _comparison(self) -> ast.Expr:
        """Parses comparison expressions (>, >=, <, <=)."""
        expr = self._term()
        while self._match(TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL):
            operator = self._previous()
            right = self._term()
            expr = ast.Binary(expr, operator, right)
        return expr

    def _term(self) -> ast.Expr:
        """Parses addition and subtraction expressions (+, -)."""
        expr = self._factor()
        while self._match(TokenType.MINUS, TokenType.PLUS):
            operator = self._previous()
            right = self._factor()
            expr = ast.Binary(expr, operator, right)
        return expr

    def _factor(self) -> ast.Expr:
        """Parses multiplication and division expressions (*, /)."""
        expr = self._unary()
        while self._match(TokenType.SLASH, TokenType.STAR):
            operator = self._previous()
            right = self._unary()
            expr = ast.Binary(expr, operator, right)
        return expr

    def _unary(self) -> ast.Expr:
        """Parses unary expressions (e.g., -x)."""
        if self._match(TokenType.MINUS):
            operator = self._previous()
            right = self._unary()
            return ast.Unary(operator, right)
        return self._primary()

    def _primary(self) -> ast.Expr:
        """Parses primary expressions (literals, grouping, identifiers)."""
        if self._match(TokenType.FALSE): return ast.Literal(False)
        if self._match(TokenType.TRUE): return ast.Literal(True)

        if self._match(TokenType.NUMBER, TokenType.STRING):
            return ast.Literal(self._previous().literal)

        if self._match(TokenType.IDENTIFIER):
            return ast.Variable(self._previous())

        if self._match(TokenType.LEFT_PAREN):
            expr = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return ast.Grouping(expr)

        raise self._error(self._peek(), "Expect expression.")

    # --- TOKEN CONSUMPTION & UTILITY METHODS ---

    def _match(self, *types: TokenType) -> bool:
        """
        Checks if the current token has any of the given types.
        If so, it consumes the token and returns True.
        """
        for token_type in types:
            if self._check(token_type):
                self._advance()
                return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        """Checks if the current token is of the given type without consuming it."""
        if self._is_at_end():
            return False
        return self._peek().token_type == token_type

    def _advance(self) -> Token:
        """Consumes the current token and returns it."""
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        """Checks if we have run out of tokens to parse."""
        return self._peek().token_type == TokenType.EOF

    def _peek(self) -> Token:
        """Returns the current token without consuming it."""
        return self.tokens[self.current]

    def _previous(self) -> Token:
        """Returns the most recently consumed token."""
        return self.tokens[self.current - 1]

    # --- ERROR HANDLING & SYNCHRONIZATION ---

    def _consume(self, token_type: TokenType, message: str) -> Token:
        """
        Consumes a token of a specific type. If the next token is not of the
        expected type, it raises a ParseError.
        """
        if self._check(token_type):
            return self._advance()
        raise self._error(self._peek(), message)

    def _error(self, token: Token, message: str) -> ParseError:
        """Creates and returns a ParseError."""
        # We can enhance this to report errors more gracefully.
        line = token.line
        if token.token_type == TokenType.EOF:
            print(f"[Line {line}] Error at end: {message}")
        else:
            print(f"[Line {line}] Error at '{token.lexeme}': {message}")
        return ParseError(message)

    def _synchronize(self):
        """
        Error recovery. Discards tokens until it finds a statement boundary,
        which helps the parser continue after a syntax error.
        """
        self._advance()
        while not self._is_at_end():
            if self._previous().token_type == TokenType.SEMICOLON:
                return

            # Also look for tokens that can start a new statement
            if self._peek().token_type in [
                TokenType.FUNCTION,
                TokenType.VAR,
                TokenType.FOR,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.COMPONENT,
                TokenType.RETURN
            ]:
                return

            self._advance()
