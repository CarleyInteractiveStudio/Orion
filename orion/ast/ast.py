from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

from orion.lexer.token import Token

# Base Nodes

class Node(ABC):
    @abstractmethod
    def token_literal(self) -> str:
        """Returns the literal value of the token associated with this node."""
        pass

    def __str__(self) -> str:
        return self.token_literal()

class Statement(Node):
    pass

class Expression(Node):
    pass

# Root Node

@dataclass
class Program(Node):
    statements: List[Statement]

    def token_literal(self) -> str:
        if self.statements:
            return self.statements[0].token_literal()
        return ""

    def __str__(self) -> str:
        return "".join(str(s) for s in self.statements)

# Expressions

@dataclass
class Identifier(Expression):
    token: Token  # the TokenType.IDENT token
    value: str

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return self.value

@dataclass
class IntegerLiteral(Expression):
    token: Token
    value: int

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return str(self.value)

@dataclass
class PrefixExpression(Expression):
    token: Token  # The prefix token, e.g. !, -
    operator: str
    right: Expression

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return f"({self.operator}{str(self.right)})"

@dataclass
class Boolean(Expression):
    token: Token
    value: bool

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return self.token.literal

@dataclass
class InfixExpression(Expression):
    token: Token  # The operator token, e.g. +
    left: Expression
    operator: str
    right: Expression

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return f"({str(self.left)} {self.operator} {str(self.right)})"

@dataclass
class StringLiteral(Expression):
    token: Token
    value: str

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return self.token.literal

@dataclass
class CallExpression(Expression):
    token: Token  # The '(' token
    function: Expression  # Identifier or FunctionLiteral
    arguments: List[Expression]

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        args = ", ".join(str(a) for a in self.arguments)
        return f"{self.function}({args})"

@dataclass
class MemberAccessExpression(Expression):
    token: Token # The '.' token
    object: Expression
    property: Identifier

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return f"({self.object}.{self.property})"

# Statements

@dataclass
class VarStatement(Statement):
    token: Token  # The 'var', 'let', or 'const' token
    name: Identifier
    value: Optional[Expression] = None

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        s = f"{self.token_literal()} {self.name} = "
        if self.value:
            s += str(self.value)
        s += ";"
        return s

@dataclass
class ReturnStatement(Statement):
    token: Token  # The 'return' token
    return_value: Optional[Expression] = None

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        s = f"{self.token_literal()} "
        if self.return_value:
            s += str(self.return_value)
        s += ";"
        return s

@dataclass
class ExpressionStatement(Statement):
    token: Token  # The first token of the expression
    expression: Expression

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return str(self.expression)

@dataclass
class ModuleStatement(Statement):
    token: Token # The 'module' token
    name: Identifier

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return f"module {self.name};"

@dataclass
class UseStatement(Statement):
    token: Token # The 'use' token
    path: Expression # Could be Identifier or something like UI.Button
    alias: Optional[Identifier] = None

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        s = f"use {self.path}"
        if self.alias:
            s += f" as {self.alias}"
        s += ";"
        return s

@dataclass
class BlockStatement(Statement):
    token: Token  # the { token
    statements: List[Statement]

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return "".join(str(s) for s in self.statements)

@dataclass
class FunctionStatement(Statement):
    token: Token  # The 'function' token
    name: Identifier
    parameters: List[Identifier]
    body: BlockStatement

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        params = ", ".join(str(p) for p in self.parameters)
        return f"function {self.name}({params}) {{ {self.body} }}"

@dataclass
class IfStatement(Statement):
    token: Token  # The 'if' token
    condition: Expression
    consequence: BlockStatement
    alternative: Optional[BlockStatement] = None

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        s = f"if {self.condition} {self.consequence}"
        if self.alternative:
            s += f" else {self.alternative}"
        return s

@dataclass
class StyleProperty(Statement):
    token: Token # the property name token
    name: Identifier
    values: List[Expression]

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        vals = ", ".join(str(v) for v in self.values)
        return f"{self.name}: {vals};"

@dataclass
class ComponentStatement(Statement):
    token: Token # The 'component' token
    name: Identifier
    body: List[Statement] # Can contain StyleProperty or nested components

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        body_str = "".join(str(s) for s in self.body)
        return f"component {self.name} {{ {body_str} }}"

@dataclass
class HexLiteral(Expression):
    token: Token # The '#' token
    value: str

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return f"#{self.value}"
