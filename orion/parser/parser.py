from orion.lexer.lexer import Lexer
from orion.lexer.token import Token, TokenType
from orion.ast.ast import (
    Program, Statement, VarStatement, Identifier, ReturnStatement,
    ExpressionStatement, Expression, IntegerLiteral, PrefixExpression,
    InfixExpression, ModuleStatement, UseStatement, BlockStatement,
    FunctionStatement, IfStatement, StringLiteral, CallExpression,
    MemberAccessExpression, ComponentStatement, StyleProperty, HexLiteral,
    Boolean, FunctionLiteral
)

# Operator precedence constants
LOWEST = 1
EQUALS = 2       # ==
LESSGREATER = 3  # > or <
SUM = 4          # +
PRODUCT = 5      # *
PREFIX = 6       # -X or !X
CALL = 7         # myFunction(X)
MEMBER = 8       # object.property

precedences = {
    TokenType.EQ: EQUALS,
    TokenType.NOT_EQ: EQUALS,
    TokenType.LT: LESSGREATER,
    TokenType.GT: LESSGREATER,
    TokenType.PLUS: SUM,
    TokenType.MINUS: SUM,
    TokenType.SLASH: PRODUCT,
    TokenType.ASTERISK: PRODUCT,
    TokenType.LPAREN: CALL,
    TokenType.DOT: MEMBER,
}

class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.errors: list[str] = []

        self.current_token: Token = None
        self.peek_token: Token = None

        # Read two tokens, so current_token and peek_token are both set
        self.next_token()
        self.next_token()

        # Registering parsing functions
        self.prefix_parse_fns = {
            TokenType.IDENT: self.parse_identifier,
            TokenType.INT: self.parse_integer_literal,
            TokenType.BANG: self.parse_prefix_expression,
            TokenType.MINUS: self.parse_prefix_expression,
            TokenType.STRING: self.parse_string_literal,
            TokenType.HASH: self.parse_hash_literal,
            TokenType.TRUE: self.parse_boolean,
            TokenType.FALSE: self.parse_boolean,
            TokenType.FUNCTION: self.parse_function_literal,
        }
        self.prefix_parse_fns[TokenType.LPAREN] = self.parse_grouped_expression
        self.infix_parse_fns = {
            TokenType.PLUS: self.parse_infix_expression,
            TokenType.MINUS: self.parse_infix_expression,
            TokenType.SLASH: self.parse_infix_expression,
            TokenType.ASTERISK: self.parse_infix_expression,
            TokenType.EQ: self.parse_infix_expression,
            TokenType.NOT_EQ: self.parse_infix_expression,
            TokenType.LT: self.parse_infix_expression,
            TokenType.GT: self.parse_infix_expression,
            TokenType.LPAREN: self.parse_call_expression,
            TokenType.DOT: self.parse_member_access_expression,
        }

    def next_token(self):
        """Advances the tokens."""
        self.current_token = self.peek_token
        self.peek_token = self.lexer.next_token()

    def parse_program(self) -> Program:
        """
        The main entry point for the parser. Parses the entire program.
        """
        program = Program(statements=[])

        while not self.current_token_is(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt is not None:
                program.statements.append(stmt)
            self.next_token()

        return program

    def parse_statement(self) -> Statement | None:
        """
        Parses a single statement based on the current token.
        """
        if self.current_token_is(TokenType.MODULE):
            return self.parse_module_statement()
        elif self.current_token_is(TokenType.USE):
            return self.parse_use_statement()
        elif self.current_token_is(TokenType.FUNCTION):
            return self.parse_function_statement()
        elif self.current_token_is(TokenType.COMPONENT):
            return self.parse_component_statement()
        elif self.current_token_is(TokenType.IF):
            return self.parse_if_statement()
        elif self.current_token_is(TokenType.VAR) or self.current_token_is(TokenType.LET) or self.current_token_is(TokenType.CONST):
            return self.parse_var_statement()
        elif self.current_token_is(TokenType.RETURN):
            return self.parse_return_statement()
        else:
            return self.parse_expression_statement()

    def parse_module_statement(self) -> ModuleStatement | None:
        token = self.current_token
        if not self.expect_peek(TokenType.IDENT):
            return None

        name = Identifier(token=self.current_token, value=self.current_token.literal)
        stmt = ModuleStatement(token=token, name=name)

        if not self.expect_peek(TokenType.SEMICOLON):
            return None # Or handle optional semicolon

        return stmt

    def parse_use_statement(self) -> UseStatement | None:
        token = self.current_token
        if not self.expect_peek(TokenType.IDENT):
            return None

        # For now, we only parse simple identifiers like 'UI'
        # A more complex path like 'UI.Buttons' would require expression parsing here
        path = self.parse_identifier()
        stmt = UseStatement(token=token, path=path)

        if not self.expect_peek(TokenType.SEMICOLON):
            return None

        return stmt

    def parse_function_statement(self) -> FunctionStatement | None:
        token = self.current_token # 'function' token
        if not self.expect_peek(TokenType.IDENT):
            return None

        name = Identifier(token=self.current_token, value=self.current_token.literal)

        if not self.expect_peek(TokenType.LPAREN):
            return None

        parameters = self.parse_function_parameters()

        if not self.expect_peek(TokenType.LBRACE):
            return None

        body = self.parse_block_statement()

        return FunctionStatement(token=token, name=name, parameters=parameters, body=body)

    def parse_function_parameters(self) -> list[Identifier]:
        params = []
        if self.peek_token_is(TokenType.RPAREN):
            self.next_token()
            return params

        self.next_token()

        param = Identifier(token=self.current_token, value=self.current_token.literal)
        params.append(param)

        while self.peek_token_is(TokenType.COMMA):
            self.next_token()
            self.next_token()
            param = Identifier(token=self.current_token, value=self.current_token.literal)
            params.append(param)

        if not self.expect_peek(TokenType.RPAREN):
            return None

        return params

    def parse_block_statement(self) -> BlockStatement:
        block = BlockStatement(token=self.current_token, statements=[])
        self.next_token() # move past {

        while not self.current_token_is(TokenType.RBRACE) and not self.current_token_is(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt is not None:
                block.statements.append(stmt)
            self.next_token()

        return block

    def parse_if_statement(self) -> IfStatement | None:
        token = self.current_token # 'if' token
        if not self.expect_peek(TokenType.LPAREN):
            return None

        self.next_token()
        condition = self.parse_expression(LOWEST)

        if not self.expect_peek(TokenType.RPAREN):
            return None

        if not self.expect_peek(TokenType.LBRACE):
            return None

        consequence = self.parse_block_statement()

        # Check for else block
        alternative = None
        if self.peek_token_is(TokenType.ELSE):
            self.next_token()
            if not self.expect_peek(TokenType.LBRACE):
                return None
            alternative = self.parse_block_statement()

        return IfStatement(token=token, condition=condition, consequence=consequence, alternative=alternative)

    def parse_grouped_expression(self) -> Expression:
        self.next_token() # move past (

        exp = self.parse_expression(LOWEST)

        if not self.expect_peek(TokenType.RPAREN):
            return None

        return exp

    def parse_boolean(self) -> Expression:
        return Boolean(token=self.current_token, value=self.current_token_is(TokenType.TRUE))

    def parse_function_literal(self) -> Expression:
        token = self.current_token # 'function' token

        if not self.expect_peek(TokenType.LPAREN):
            return None

        parameters = self.parse_function_parameters()

        if not self.expect_peek(TokenType.LBRACE):
            return None

        body = self.parse_block_statement()

        return FunctionLiteral(token=token, parameters=parameters, body=body)

    def parse_string_literal(self) -> Expression:
        return StringLiteral(token=self.current_token, value=self.current_token.literal)

    def parse_call_expression(self, function: Expression) -> Expression:
        token = self.current_token
        arguments = self.parse_expression_list(TokenType.RPAREN)
        return CallExpression(token=token, function=function, arguments=arguments)

    def parse_expression_list(self, end_token: TokenType) -> list[Expression]:
        args = []
        if self.peek_token_is(end_token):
            self.next_token()
            return args

        self.next_token()
        args.append(self.parse_expression(LOWEST))

        while self.peek_token_is(TokenType.COMMA):
            self.next_token()
            self.next_token()
            args.append(self.parse_expression(LOWEST))

        if not self.expect_peek(end_token):
            return None

        return args

    def parse_member_access_expression(self, obj: Expression) -> Expression:
        token = self.current_token
        if not self.expect_peek(TokenType.IDENT):
            return None

        prop = self.parse_identifier()

        return MemberAccessExpression(token=token, object=obj, property=prop)

    def parse_component_statement(self) -> ComponentStatement | None:
        token = self.current_token # 'component' token
        if not self.expect_peek(TokenType.IDENT):
            return None

        name = self.parse_identifier()

        if not self.expect_peek(TokenType.LBRACE):
            return None

        body = self.parse_component_body()

        return ComponentStatement(token=token, name=name, body=body)

    def parse_component_body(self) -> list[Statement]:
        body = []
        self.next_token() # Consume '{'

        while not self.current_token_is(TokenType.RBRACE) and not self.current_token_is(TokenType.EOF):
            stmt = None
            if self.current_token_is(TokenType.IDENT) and self.peek_token_is(TokenType.COLON):
                prop_name = self.parse_identifier()
                self.next_token() # consume ':'
                self.next_token() # move to value

                values = []
                while not self.current_token_is(TokenType.SEMICOLON):
                    if self.current_token_is(TokenType.INT) and self.peek_token_is(TokenType.IDENT):
                         val = StringLiteral(token=self.current_token, value=f"{self.current_token.literal}{self.peek_token.literal}")
                         self.next_token()
                         values.append(val)
                    else:
                        values.append(self.parse_expression(LOWEST))

                    if self.peek_token_is(TokenType.COMMA):
                        self.next_token()

                    self.next_token()

                stmt = StyleProperty(token=prop_name.token, name=prop_name, values=values)

            elif self.current_token_is(TokenType.IDENT) and self.peek_token_is(TokenType.LBRACE):
                stmt = self.parse_nested_style_block()

            if stmt is not None:
                body.append(stmt)
            else:
                # If no statement was parsed, advance to avoid infinite loop on error
                self.next_token()

        return body

    def parse_nested_style_block(self) -> ComponentStatement:
        token = self.current_token # e.g. 'warning'
        name = self.parse_identifier()
        if not self.expect_peek(TokenType.LBRACE):
            return None
        body = self.parse_component_body()
        # We reuse ComponentStatement for simplicity, though it's not a full component
        return ComponentStatement(token=token, name=name, body=body)

    def parse_hash_literal(self) -> Expression:
        token = self.current_token
        if not self.peek_token_is(TokenType.IDENT) and not self.peek_token_is(TokenType.INT):
            self.errors.append("expected identifier or integer after #")
            return None
        self.next_token()
        return HexLiteral(token=token, value=self.current_token.literal)

    def parse_var_statement(self) -> VarStatement | None:
        var_token = self.current_token

        if not self.expect_peek(TokenType.IDENT):
            return None

        name_identifier = Identifier(token=self.current_token, value=self.current_token.literal)

        if not self.expect_peek(TokenType.ASSIGN):
            # This could be a declaration without assignment, e.g. `var x;`
            # For now, we assume all declarations have assignments.
            return None

        self.next_token()

        value_expression = self.parse_expression(LOWEST)

        stmt = VarStatement(token=var_token, name=name_identifier, value=value_expression)

        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()

        return stmt

    def parse_return_statement(self) -> ReturnStatement | None:
        stmt = ReturnStatement(token=self.current_token)
        self.next_token()

        stmt.return_value = self.parse_expression(LOWEST)

        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()

        return stmt

    def parse_expression_statement(self) -> ExpressionStatement:
        token = self.current_token
        expression = self.parse_expression(LOWEST)

        stmt = ExpressionStatement(token=token, expression=expression)

        # Optional semicolon
        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()

        return stmt

    def parse_expression(self, precedence: int) -> Expression | None:
        prefix = self.prefix_parse_fns.get(self.current_token.token_type)
        if prefix is None:
            self.no_prefix_parse_fn_error(self.current_token.token_type)
            return None

        left_exp = prefix()

        while not self.peek_token_is(TokenType.SEMICOLON) and precedence < self.peek_precedence():
            infix = self.infix_parse_fns.get(self.peek_token.token_type)
            if infix is None:
                return left_exp

            self.next_token()
            left_exp = infix(left_exp)

        return left_exp

    # --- Prefix parsing functions ---

    def parse_identifier(self) -> Expression:
        return Identifier(token=self.current_token, value=self.current_token.literal)

    def parse_integer_literal(self) -> Expression | None:
        token = self.current_token
        try:
            value = int(token.literal)
            return IntegerLiteral(token=token, value=value)
        except ValueError:
            msg = f"could not parse {token.literal} as integer"
            self.errors.append(msg)
            return None

    def parse_prefix_expression(self) -> Expression:
        token = self.current_token
        operator = self.current_token.literal

        self.next_token()

        right = self.parse_expression(PREFIX)

        return PrefixExpression(token=token, operator=operator, right=right)

    def parse_infix_expression(self, left: Expression) -> Expression:
        token = self.current_token
        operator = self.current_token.literal
        precedence = self.current_precedence()

        self.next_token()

        right = self.parse_expression(precedence)

        return InfixExpression(token=token, left=left, operator=operator, right=right)

    def no_prefix_parse_fn_error(self, t: TokenType):
        self.errors.append(f"no prefix parse function for {t.name} found")

    # --- Helper methods ---

    def current_token_is(self, t: TokenType) -> bool:
        """Checks the type of the current token."""
        return self.current_token.token_type == t

    def peek_token_is(self, t: TokenType) -> bool:
        """Checks the type of the peek token."""
        return self.peek_token.token_type == t

    def expect_peek(self, t: TokenType) -> bool:
        """
        Asserts the type of the next token and advances if correct.
        If not, it records an error.
        """
        if self.peek_token_is(t):
            self.next_token()
            return True
        else:
            self.peek_error(t)
            return False

    def peek_error(self, t: TokenType):
        """Adds an error when the peek token is not what was expected."""
        msg = (
            f"expected next token to be {t.name}, "
            f"got {self.peek_token.token_type.name} instead"
        )
        self.errors.append(msg)

    def peek_precedence(self) -> int:
        return precedences.get(self.peek_token.token_type, LOWEST)

    def current_precedence(self) -> int:
        return precedences.get(self.current_token.token_type, LOWEST)
