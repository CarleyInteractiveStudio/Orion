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
            if self._match(TokenType.MODULE):
                return self._module_statement()
            if self._match(TokenType.USE):
                return self._use_statement()
            if self._match(TokenType.COMPONENT):
                return self._component_declaration()
            if self._match(TokenType.FUNCTION):
                return self._function("function")
            if self._match(TokenType.VAR, TokenType.LET):
                return self._var_declaration(is_const=False)
            if self._match(TokenType.CONST):
                return self._var_declaration(is_const=True)
            return self._statement()
        except ParseError:
            self._synchronize()
            return None

    def _var_declaration(self, is_const: bool) -> ast.Stmt:
        """Parses a variable declaration: ('var'|'let'|'const') IDENTIFIER (':' type)? ('=' expression)? ';'"""
        name = self._consume(TokenType.IDENTIFIER, "Expect variable name.")

        type_annotation: Optional[ast.Expr] = None
        if self._match(TokenType.COLON):
            type_annotation = self._type_annotation()

        initializer: Optional[ast.Expr] = None
        if self._match(TokenType.EQUAL):
            initializer = self._expression()

        if is_const and initializer is None:
            self._error(name, "Constant variables must be initialized.")

        self._consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return ast.Var(name, type_annotation, initializer, is_const)

    def _statement(self) -> ast.Stmt:
        """Parses a statement. This includes if, while, return, for, expression, and block statements."""
        if self._match(TokenType.FOR):
            return self._for_statement()
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.RETURN):
            return self._return_statement()
        if self._match(TokenType.WHILE):
            return self._while_statement()
        if self._match(TokenType.LEFT_BRACE):
            return ast.Block(self._block())
        return self._expression_statement()

    def _if_statement(self) -> ast.Stmt:
        """Parses an if-else statement."""
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")

        then_branch = self._statement()
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self._statement()

        return ast.If(condition, then_branch, else_branch)

    def _for_statement(self) -> ast.Stmt:
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        # Initializer
        initializer: Optional[ast.Stmt]
        if self._match(TokenType.SEMICOLON):
            initializer = None
        elif self._match(TokenType.VAR):
            initializer = self._var_declaration(is_const=False)
        else:
            initializer = self._expression_statement()

        # Condition
        condition: Optional[ast.Expr] = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        # Increment
        increment: Optional[ast.Expr] = None
        if not self._check(TokenType.RIGHT_PAREN):
            increment = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")

        body = self._statement()

        # Desugaring
        if increment is not None:
            body = ast.Block(statements=[body, ast.Expression(increment)])

        if condition is None:
            condition = ast.Literal(True)
        body = ast.While(condition, body)

        if initializer is not None:
            body = ast.Block(statements=[initializer, body])

        return body

    def _while_statement(self) -> ast.Stmt:
        """Parses a while loop."""
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after while condition.")
        body = self._statement()

        return ast.While(condition, body)

    def _return_statement(self) -> ast.Stmt:
        """Parses a return statement."""
        keyword = self._previous()
        value = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()

        self._consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return ast.Return(keyword, value)

    def _function(self, kind: str) -> ast.Function:
        """Parses a function declaration."""
        name = self._consume(TokenType.IDENTIFIER, f"Expect {kind} name.")
        self._consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")

        parameters: List[ast.Param] = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                if len(parameters) >= 255:
                    self._error(self._peek(), "Can't have more than 255 parameters.")

                param_name = self._consume(TokenType.IDENTIFIER, "Expect parameter name.")
                param_type = None
                if self._match(TokenType.COLON):
                    param_type = self._type_annotation()
                parameters.append(ast.Param(param_name, param_type))

                if not self._match(TokenType.COMMA):
                    break

        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")

        return_type: Optional[ast.Expr] = None
        if self._match(TokenType.COLON):
            return_type = self._type_annotation()

        self._consume(TokenType.LEFT_BRACE, f"Expect '{{' before {kind} body.")
        body = self._block()
        return ast.Function(name, parameters, body, return_type)

    def _module_statement(self) -> ast.Stmt:
        """Parses a module declaration."""
        name = self._consume(TokenType.IDENTIFIER, "Expect module name.")
        self._consume(TokenType.SEMICOLON, "Expect ';' after module name.")
        return ast.ModuleStmt(name)

    def _use_statement(self) -> ast.Stmt:
        """Parses a use/import statement."""
        name = self._consume(TokenType.IDENTIFIER, "Expect module name to use.")

        alias = None
        if self._match(TokenType.AS):
            alias = self._consume(TokenType.IDENTIFIER, "Expect alias name after 'as'.")

        self._consume(TokenType.SEMICOLON, "Expect ';' after use statement.")
        return ast.UseStmt(name, alias)

    def _component_declaration(self) -> ast.Stmt:
        """Parses a component declaration."""
        name = self._consume(TokenType.IDENTIFIER, "Expect component name.")
        self._consume(TokenType.LEFT_BRACE, "Expect '{' before component body.")

        body = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            body.append(self._component_body_statement())

        self._consume(TokenType.RIGHT_BRACE, "Expect '}' after component body.")
        return ast.ComponentStmt(name, body)

    def _component_body_statement(self) -> ast.Stmt:
        """Parses a statement inside a component body (method, style prop, or state block)."""
        if self._match(TokenType.FUNCTION):
            return self._function("method")

        if self._check(TokenType.IDENTIFIER) and self._check_next(TokenType.LEFT_BRACE):
            return self._state_block()

        # For now, we assume anything else is a style property.
        # We could add var/const declarations here later.
        return self._style_property()

    def _state_block(self) -> ast.Stmt:
        """Parses a nested state block like 'hover { ... }'."""
        name = self._consume(TokenType.IDENTIFIER, "Expect state name.")
        self._consume(TokenType.LEFT_BRACE, "Expect '{' before state block body.")

        props = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            props.append(self._style_property())

        self._consume(TokenType.RIGHT_BRACE, "Expect '}' after state block body.")
        return ast.StateBlock(name, props)

    def _style_property(self) -> ast.Stmt:
        """Parses a style property like 'name: value1, value2;'."""
        name = self._consume(TokenType.IDENTIFIER, "Expect property name.")
        self._consume(TokenType.COLON, "Expect ':' after property name.")

        values = []
        while not self._check(TokenType.SEMICOLON) and not self._is_at_end():
            if len(values) > 0 and self._peek().token_type != TokenType.COMMA:
                pass

            if self._peek().token_type == TokenType.COMMA:
                 self._consume(TokenType.COMMA, "Unexpected comma.")
                 continue

            values.append(self._advance())

        self._consume(TokenType.SEMICOLON, "Expect ';' after property value.")
        return ast.StyleProp(name, values)

    def _check_next(self, token_type: TokenType) -> bool:
        """Checks the type of the token after the current one."""
        if self._is_at_end(): return False
        if self.tokens[self.current + 1].token_type == TokenType.EOF: return False
        return self.tokens[self.current + 1].token_type == token_type

    def _block(self) -> List[ast.Stmt]:
        """Parses a block of statements."""
        statements: List[ast.Stmt] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            declaration = self._declaration()
            if declaration is not None:
                statements.append(declaration)

        self._consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def _expression_statement(self) -> ast.Stmt:
        """Parses an expression statement: expression ';'"""
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return ast.Expression(expr)

    def _expression(self) -> ast.Expr:
        """Parses an expression. Entry point for all expression rules."""
        return self._assignment()

    def _assignment(self) -> ast.Expr:
        """Parses an assignment expression."""
        expr = self._or()

        if self._match(TokenType.EQUAL):
            equals = self._previous()
            value = self._assignment()

            if isinstance(expr, ast.Variable):
                return ast.Assign(expr.name, value)
            elif isinstance(expr, ast.Get):
                return ast.Set(expr.object, expr.name, value)
            elif isinstance(expr, ast.GetSubscript):
                return ast.SetSubscript(expr.object, expr.index, value, expr.bracket)

            self._error(equals, "Invalid assignment target.")

        return expr

    def _or(self) -> ast.Expr:
        """Parses logical OR expressions."""
        expr = self._and()
        while self._match(TokenType.OR):
            operator = self._previous()
            right = self._and()
            expr = ast.Logical(expr, operator, right)
        return expr

    def _and(self) -> ast.Expr:
        """Parses logical AND expressions."""
        expr = self._equality()
        while self._match(TokenType.AND):
            operator = self._previous()
            right = self._equality()
            expr = ast.Logical(expr, operator, right)
        return expr

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
        """Parses unary expressions (e.g., -x, !y)."""
        if self._match(TokenType.MINUS, TokenType.BANG):
            operator = self._previous()
            right = self._unary()
            return ast.Unary(operator, right)
        return self._call()

    def _finish_call(self, callee: ast.Expr) -> ast.Expr:
        """Helper to parse the argument list of a function call."""
        arguments: List[ast.Expr] = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                if len(arguments) >= 255:
                    self._error(self._peek(), "Can't have more than 255 arguments.")
                arguments.append(self._expression())
                if not self._match(TokenType.COMMA):
                    break

        paren = self._consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")
        return ast.Call(callee, paren, arguments)

    def _call(self) -> ast.Expr:
        """Parses a function call, property access, or subscript expression."""
        expr = self._primary()

        while True:
            if self._match(TokenType.LEFT_PAREN):
                expr = self._finish_call(expr)
            elif self._match(TokenType.DOT):
                name = self._consume(TokenType.IDENTIFIER, "Expect property name after '.'.")
                expr = ast.Get(expr, name)
            elif self._match(TokenType.LEFT_BRACKET):
                index = self._expression()
                bracket = self._consume(TokenType.RIGHT_BRACKET, "Expect ']' after index.")
                expr = ast.GetSubscript(expr, index, bracket)
            else:
                break

        return expr

    def _primary(self) -> ast.Expr:
        """Parses primary expressions (literals, grouping, identifiers, lists)."""
        if self._match(TokenType.FALSE): return ast.Literal(False)
        if self._match(TokenType.TRUE): return ast.Literal(True)
        if self._match(TokenType.THIS): return ast.This(self._previous())

        if self._match(TokenType.NUMBER, TokenType.STRING):
            return ast.Literal(self._previous().literal)

        if self._match(TokenType.INT, TokenType.FLOAT, TokenType.BOOL, TokenType.STRING_TYPE):
            return ast.Variable(self._previous())

        if self._match(TokenType.IDENTIFIER):
            return ast.Variable(self._previous())

        if self._match(TokenType.LEFT_PAREN):
            expr = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return ast.Grouping(expr)

        if self._match(TokenType.LEFT_BRACKET):
            elements = []
            if not self._check(TokenType.RIGHT_BRACKET):
                while True:
                    elements.append(self._expression())
                    if not self._match(TokenType.COMMA):
                        break
            self._consume(TokenType.RIGHT_BRACKET, "Expect ']' after list elements.")
            return ast.ListLiteral(elements)

        if self._match(TokenType.LEFT_BRACE):
            keys = []
            values = []
            if not self._check(TokenType.RIGHT_BRACE):
                while True:
                    key = self._consume(TokenType.STRING, "Dictionary keys must be strings.")
                    self._consume(TokenType.COLON, "Expect ':' after dictionary key.")
                    value = self._expression()

                    keys.append(ast.Literal(key.literal))
                    values.append(value)

                    if not self._match(TokenType.COMMA):
                        break
            self._consume(TokenType.RIGHT_BRACE, "Expect '}' after dictionary.")
            return ast.DictLiteral(keys, values)

        raise self._error(self._peek(), "Expect expression.")

    def _type_annotation(self) -> ast.Expr:
        """Parses a type annotation, which can be simple or generic."""
        base_type = self._primary()

        if self._match(TokenType.LEFT_BRACKET):
            params = []
            if not self._check(TokenType.RIGHT_BRACKET):
                while True:
                    params.append(self._type_annotation())
                    if not self._match(TokenType.COMMA):
                        break
            self._consume(TokenType.RIGHT_BRACKET, "Expect ']' after type parameters.")
            return ast.GenericType(base_type, params)

        return base_type

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
