from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from dataclasses import dataclass

from orion.lexer.token import Token

# --- Base Nodes ---
class Node(ABC):
    @abstractmethod
    def token_literal(self) -> str: pass
    def __str__(self) -> str: return self.token_literal()

class Statement(Node): pass
class Expression(Node): pass

# --- Root Node ---
@dataclass
class Program(Node):
    statements: List[Statement]
    def token_literal(self) -> str: return self.statements[0].token_literal() if self.statements else ""
    def __str__(self) -> str: return "".join(str(s) for s in self.statements)

# --- Expressions ---
@dataclass
class Identifier(Expression):
    token: Token; value: str
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return self.value

@dataclass
class IntegerLiteral(Expression):
    token: Token; value: int
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return str(self.value)

@dataclass
class StringLiteral(Expression):
    token: Token; value: str
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return self.token.literal

@dataclass
class Boolean(Expression):
    token: Token; value: bool
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return self.token.literal.lower()

@dataclass
class ArrayLiteral(Expression):
    token: Token; elements: List[Expression]
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return f"[{', '.join(str(e) for e in self.elements)}]"

from typing import Tuple

@dataclass
class HashLiteral(Expression):
    token: Token; pairs: List[Tuple[Expression, Expression]]
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return f"{{{', '.join(f'{k}:{v}' for k, v in self.pairs)}}}"

@dataclass
class FunctionLiteral(Expression):
    token: Token; parameters: List[Identifier]; body: 'BlockStatement'
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return f"function({', '.join(str(p) for p in self.parameters)}) {{ {self.body} }}"

@dataclass
class PrefixExpression(Expression):
    token: Token; operator: str; right: Expression
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return f"({self.operator}{self.right})"

@dataclass
class InfixExpression(Expression):
    token: Token; left: Expression; operator: str; right: Expression
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return f"({self.left} {self.operator} {self.right})"

@dataclass
class IndexExpression(Expression):
    token: Token; left: Expression; index: Expression
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return f"({self.left}[{self.index}])"

@dataclass
class CallExpression(Expression):
    token: Token; function: Expression; arguments: List[Expression]
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return f"{self.function}({', '.join(str(a) for a in self.arguments)})"

@dataclass
class MemberAccessExpression(Expression):
    token: Token; object: Expression; property: Identifier
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return f"({self.object}.{self.property})"

@dataclass
class DimensionLiteral(Expression):
    token: Token; value: str
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return self.value

# --- Statements ---
@dataclass
class BlockStatement(Statement):
    token: Token; statements: List[Statement]
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return "".join(str(s) for s in self.statements)

@dataclass
class VarStatement(Statement):
    token: Token; name: Identifier; value: Optional[Expression] = None
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return f"{self.token_literal()} {self.name} = {self.value if self.value else ''};"

@dataclass
class ReturnStatement(Statement):
    token: Token; return_value: Optional[Expression] = None
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return f"{self.token_literal()} {self.return_value if self.return_value else ''};"

@dataclass
class ExpressionStatement(Statement):
    token: Token; expression: Expression
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return str(self.expression)

@dataclass
class ModuleStatement(Statement):
    token: Token; name: Identifier
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return f"module {self.name};"

@dataclass
class UseStatement(Statement):
    token: Token; path: Expression; alias: Optional[Identifier] = None
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str:
        s = f"use {self.path}"
        if self.alias: s += f" as {self.alias}"
        s += ";"
        return s

@dataclass
class IfStatement(Statement):
    token: Token; condition: Expression; consequence: BlockStatement; alternative: Optional[BlockStatement] = None
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return f"if {self.condition} {{ {self.consequence} }} else {{ {self.alternative if self.alternative else ''} }}"

@dataclass
class StyleProperty(Statement):
    token: Token; name: Identifier; values: List[Expression]
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return f"{self.name}: {', '.join(str(v) for v in self.values)};"

@dataclass
class ComponentStatement(Statement):
    token: Token; name: Identifier; body: List[Statement]
    def token_literal(self) -> str: return self.token.literal
    def __str__(self) -> str: return f"component {self.name} {{ {''.join(str(s) for s in self.body)} }}"
