from orion.lexer.lexer import Lexer
from orion.lexer.token import Token, TokenType
from orion.ast import ast

# --- Operator Precedence ---
LOWEST, EQUALS, LESSGREATER, SUM, PRODUCT, PREFIX, CALL, INDEX, MEMBER = range(1, 10)

precedences = {
    TokenType.EQ: EQUALS, TokenType.NOT_EQ: EQUALS,
    TokenType.LT: LESSGREATER, TokenType.GT: LESSGREATER,
    TokenType.PLUS: SUM, TokenType.MINUS: SUM,
    TokenType.SLASH: PRODUCT, TokenType.ASTERISK: PRODUCT,
    TokenType.LPAREN: CALL, TokenType.LBRACKET: INDEX,
    TokenType.DOT: MEMBER,
}

class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.errors = []
        self.current_token = None
        self.peek_token = None

        self.prefix_parse_fns = self._register_prefix_fns()
        self.infix_parse_fns = self._register_infix_fns()

        self.next_token()
        self.next_token()

    # --- Main Parsing Logic ---
    def parse_program(self) -> ast.Program:
        program = ast.Program(statements=[])
        while not self.current_token_is(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                program.statements.append(stmt)
            self.next_token()
        return program

    def parse_statement(self) -> ast.Statement:
        if self.current_token_is(TokenType.MODULE):
            return self.parse_module_statement()
        if self.current_token_is(TokenType.USE):
            return self.parse_use_statement()
        if self.current_token_is(TokenType.COMPONENT):
            return self.parse_component_statement()
        if self.current_token_is(TokenType.VAR) or self.current_token_is(TokenType.LET):
            return self.parse_var_statement()
        if self.current_token_is(TokenType.RETURN):
            return self.parse_return_statement()
        return self.parse_expression_statement()

    def parse_expression(self, precedence: int) -> ast.Expression:
        prefix = self.prefix_parse_fns.get(self.current_token.token_type)
        if not prefix:
            self.no_prefix_parse_fn_error(self.current_token.token_type)
            return None
        left_exp = prefix()

        while not self.peek_token_is(TokenType.SEMICOLON) and precedence < self.peek_precedence():
            infix = self.infix_parse_fns.get(self.peek_token.token_type)
            if not infix:
                return left_exp
            self.next_token()
            left_exp = infix(left_exp)
        return left_exp

    # --- Statement Parsers ---
    def parse_var_statement(self) -> ast.VarStatement:
        token = self.current_token
        if not self.expect_peek(TokenType.IDENT): return None
        name = ast.Identifier(token=self.current_token, value=self.current_token.literal)
        if not self.expect_peek(TokenType.ASSIGN): return None
        self.next_token()
        value = self.parse_expression(LOWEST)
        if self.peek_token_is(TokenType.SEMICOLON): self.next_token()
        return ast.VarStatement(token=token, name=name, value=value)

    def parse_return_statement(self) -> ast.ReturnStatement:
        stmt = ast.ReturnStatement(token=self.current_token)
        self.next_token()
        stmt.return_value = self.parse_expression(LOWEST)
        if self.peek_token_is(TokenType.SEMICOLON): self.next_token()
        return stmt

    def parse_expression_statement(self) -> ast.ExpressionStatement:
        stmt = ast.ExpressionStatement(token=self.current_token, expression=self.parse_expression(LOWEST))
        if self.peek_token_is(TokenType.SEMICOLON): self.next_token()
        return stmt

    def parse_module_statement(self) -> ast.ModuleStatement:
        token = self.current_token
        if not self.expect_peek(TokenType.IDENT): return None
        name = ast.Identifier(token=self.current_token, value=self.current_token.literal)
        if not self.expect_peek(TokenType.SEMICOLON): return None
        return ast.ModuleStatement(token=token, name=name)

    def parse_use_statement(self) -> ast.UseStatement:
        token = self.current_token
        if not self.expect_peek(TokenType.IDENT): return None
        path = ast.Identifier(token=self.current_token, value=self.current_token.literal)
        if not self.expect_peek(TokenType.SEMICOLON): return None
        return ast.UseStatement(token=token, path=path)

    def parse_component_statement(self) -> ast.ComponentStatement:
        token = self.current_token # The 'component' token
        if not self.expect_peek(TokenType.IDENT): return None
        name = ast.Identifier(token=self.current_token, value=self.current_token.literal)

        if not self.expect_peek(TokenType.LBRACE): return None

        body = []
        # The LBRACE is consumed, now we are at the first token of the body
        while not self.current_token_is(TokenType.RBRACE) and not self.current_token_is(TokenType.EOF):
            stmt = self.parse_component_level_statement()
            if stmt:
                body.append(stmt)
            self.next_token() # Advance to the next token after a statement

        # current_token should be RBRACE here
        return ast.ComponentStatement(token=token, name=name, body=body)

    def parse_component_level_statement(self) -> ast.Statement:
        if self.current_token_is(TokenType.IDENT) and self.peek_token_is(TokenType.COLON):
            return self.parse_style_property()
        if self.current_token_is(TokenType.IDENT) and self.peek_token_is(TokenType.LBRACE):
            return self.parse_nested_block()

        self.errors.append(f"Invalid statement starting with '{self.current_token.literal}' in component body")
        return None

    def parse_style_property(self) -> ast.StyleProperty:
        name_token = self.current_token
        name = ast.Identifier(token=name_token, value=name_token.literal)

        if not self.expect_peek(TokenType.COLON): return None
        self.next_token() # Move to first value

        values = self.parse_expression_list(TokenType.SEMICOLON)
        # parse_expression_list now leaves us on the SEMICOLON token.
        return ast.StyleProperty(token=name_token, name=name, values=values)

    def parse_nested_block(self) -> ast.ComponentStatement:
        token = self.current_token
        name = ast.Identifier(token=token, value=token.literal)

        if not self.expect_peek(TokenType.LBRACE): return None

        body = []
        while not self.current_token_is(TokenType.RBRACE) and not self.current_token_is(TokenType.EOF):
            self.next_token()
            if self.current_token_is(TokenType.RBRACE): break
            stmt = self.parse_component_level_statement()
            if stmt:
                body.append(stmt)

        # current_token is RBRACE
        return ast.ComponentStatement(token=token, name=name, body=body)

    def parse_block_statement(self) -> ast.BlockStatement:
        block = ast.BlockStatement(token=self.current_token, statements=[])
        self.next_token()
        while not self.current_token_is(TokenType.RBRACE) and not self.current_token_is(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                block.statements.append(stmt)
            self.next_token()
        return block

    # --- Expression Parsers (Prefix) ---
    def parse_identifier(self) -> ast.Expression: return ast.Identifier(token=self.current_token, value=self.current_token.literal)
    def parse_integer_literal(self) -> ast.Expression: return ast.IntegerLiteral(token=self.current_token, value=int(self.current_token.literal))
    def parse_string_literal(self) -> ast.Expression: return ast.StringLiteral(token=self.current_token, value=self.current_token.literal)
    def parse_dimension_literal(self) -> ast.Expression: return ast.DimensionLiteral(token=self.current_token, value=self.current_token.literal)
    def parse_boolean(self) -> ast.Expression: return ast.Boolean(token=self.current_token, value=self.current_token_is(TokenType.TRUE))
    def parse_prefix_expression(self) -> ast.Expression:
        token = self.current_token
        operator = self.current_token.literal
        self.next_token()
        right = self.parse_expression(PREFIX)
        return ast.PrefixExpression(token=token, operator=operator, right=right)
    def parse_grouped_expression(self) -> ast.Expression:
        self.next_token()
        exp = self.parse_expression(LOWEST)
        if not self.expect_peek(TokenType.RPAREN): return None
        return exp
    def parse_if_statement(self) -> ast.Expression:
        token = self.current_token
        if not self.expect_peek(TokenType.LPAREN): return None
        self.next_token()
        condition = self.parse_expression(LOWEST)
        if not self.expect_peek(TokenType.RPAREN): return None
        if not self.expect_peek(TokenType.LBRACE): return None
        consequence = self.parse_block_statement()
        alternative = None
        if self.peek_token_is(TokenType.ELSE):
            self.next_token()
            if not self.expect_peek(TokenType.LBRACE): return None
            alternative = self.parse_block_statement()
        return ast.IfStatement(token=token, condition=condition, consequence=consequence, alternative=alternative)
    def parse_function_literal(self) -> ast.Expression:
        token = self.current_token
        if not self.expect_peek(TokenType.LPAREN): return None
        parameters = self.parse_function_parameters()
        if not self.expect_peek(TokenType.LBRACE): return None
        body = self.parse_block_statement()
        return ast.FunctionLiteral(token=token, parameters=parameters, body=body)
    def parse_array_literal(self) -> ast.Expression:
        return ast.ArrayLiteral(token=self.current_token, elements=self.parse_expression_list(TokenType.RBRACKET))
    def parse_hash_literal(self) -> ast.Expression:
        h = ast.HashLiteral(token=self.current_token, pairs=[])
        while not self.peek_token_is(TokenType.RBRACE):
            self.next_token()
            key = self.parse_expression(LOWEST)
            if not self.expect_peek(TokenType.COLON): return None
            self.next_token()
            value = self.parse_expression(LOWEST)
            h.pairs.append((key, value))
            if not self.peek_token_is(TokenType.RBRACE) and not self.expect_peek(TokenType.COMMA): return None
        if not self.expect_peek(TokenType.RBRACE): return None
        return h

    # --- Expression Parsers (Infix) ---
    def parse_infix_expression(self, left: ast.Expression) -> ast.Expression:
        token = self.current_token
        operator = self.current_token.literal
        precedence = self.current_precedence()
        self.next_token()
        right = self.parse_expression(precedence)
        return ast.InfixExpression(token=token, left=left, operator=operator, right=right)
    def parse_call_expression(self, function: ast.Expression) -> ast.Expression:
        return ast.CallExpression(token=self.current_token, function=function, arguments=self.parse_expression_list(TokenType.RPAREN))
    def parse_index_expression(self, left: ast.Expression) -> ast.Expression:
        token = self.current_token
        self.next_token()
        index = self.parse_expression(LOWEST)
        if not self.expect_peek(TokenType.RBRACKET): return None
        return ast.IndexExpression(token=token, left=left, index=index)
    def parse_member_access_expression(self, left: ast.Expression) -> ast.Expression:
        token = self.current_token
        if not self.expect_peek(TokenType.IDENT): return None
        prop = ast.Identifier(token=self.current_token, value=self.current_token.literal)
        return ast.MemberAccessExpression(token=token, object=left, property=prop)

    # --- Expression Helpers ---
    def parse_expression_list(self, end: TokenType) -> list[ast.Expression]:
        elements = []
        if self.peek_token_is(end):
            self.next_token()
            return elements
        self.next_token()
        elements.append(self.parse_expression(LOWEST))
        while self.peek_token_is(TokenType.COMMA):
            self.next_token()
            self.next_token()
            elements.append(self.parse_expression(LOWEST))
        if not self.expect_peek(end): return None
        return elements
    def parse_function_parameters(self) -> list[ast.Identifier]:
        params = []
        if self.peek_token_is(TokenType.RPAREN):
            self.next_token()
            return params
        self.next_token()
        param = ast.Identifier(token=self.current_token, value=self.current_token.literal)
        params.append(param)
        while self.peek_token_is(TokenType.COMMA):
            self.next_token()
            self.next_token()
            param = ast.Identifier(token=self.current_token, value=self.current_token.literal)
            params.append(param)
        if not self.expect_peek(TokenType.RPAREN): return None
        return params

    # --- Token Helpers & Registration ---
    def _register_prefix_fns(self):
        return {
            TokenType.IDENT: self.parse_identifier, TokenType.INT: self.parse_integer_literal,
            TokenType.STRING: self.parse_string_literal, TokenType.DIMENSION: self.parse_dimension_literal,
            TokenType.TRUE: self.parse_boolean, TokenType.FALSE: self.parse_boolean,
            TokenType.BANG: self.parse_prefix_expression, TokenType.MINUS: self.parse_prefix_expression,
            TokenType.LPAREN: self.parse_grouped_expression, TokenType.IF: self.parse_if_statement,
            TokenType.FUNCTION: self.parse_function_literal, TokenType.LBRACKET: self.parse_array_literal,
            TokenType.LBRACE: self.parse_hash_literal,
        }
    def _register_infix_fns(self):
        return {
            TokenType.PLUS: self.parse_infix_expression, TokenType.MINUS: self.parse_infix_expression,
            TokenType.SLASH: self.parse_infix_expression, TokenType.ASTERISK: self.parse_infix_expression,
            TokenType.EQ: self.parse_infix_expression, TokenType.NOT_EQ: self.parse_infix_expression,
            TokenType.LT: self.parse_infix_expression, TokenType.GT: self.parse_infix_expression,
            TokenType.LPAREN: self.parse_call_expression, TokenType.LBRACKET: self.parse_index_expression,
            TokenType.DOT: self.parse_member_access_expression,
        }
    def next_token(self): self.current_token = self.peek_token; self.peek_token = self.lexer.next_token()
    def current_token_is(self, t: TokenType) -> bool: return self.current_token.token_type == t
    def peek_token_is(self, t: TokenType) -> bool: return self.peek_token.token_type == t
    def expect_peek(self, t: TokenType) -> bool:
        if self.peek_token_is(t): self.next_token(); return True
        self.peek_error(t); return False
    def peek_precedence(self) -> int: return precedences.get(self.peek_token.token_type, LOWEST)
    def current_precedence(self) -> int: return precedences.get(self.current_token.token_type, LOWEST)
    def peek_error(self, t: TokenType): self.errors.append(f"expected next token to be {t.name}, got {self.peek_token.token_type.name} instead")
    def no_prefix_parse_fn_error(self, t: TokenType): self.errors.append(f"no prefix parse function for {t.name} found")
