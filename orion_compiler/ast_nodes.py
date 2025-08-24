from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Any, Optional

from tokens import Token


# --- Visitor Pattern Definition ---

class ExprVisitor(ABC):
    @abstractmethod
    def visit_binary_expr(self, expr: 'Binary'):
        raise NotImplementedError

    @abstractmethod
    def visit_grouping_expr(self, expr: 'Grouping'):
        raise NotImplementedError

    @abstractmethod
    def visit_literal_expr(self, expr: 'Literal'):
        raise NotImplementedError

    @abstractmethod
    def visit_unary_expr(self, expr: 'Unary'):
        raise NotImplementedError

    @abstractmethod
    def visit_variable_expr(self, expr: 'Variable'):
        raise NotImplementedError


class StmtVisitor(ABC):
    @abstractmethod
    def visit_expression_stmt(self, stmt: 'Expression'):
        raise NotImplementedError

    @abstractmethod
    def visit_var_stmt(self, stmt: 'Var'):
        raise NotImplementedError


# --- Abstract Base Classes for AST Nodes ---

class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: ExprVisitor):
        raise NotImplementedError


class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor: StmtVisitor):
        raise NotImplementedError


# --- Concrete Expression Nodes ---

@dataclass
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_binary_expr(self)


@dataclass
class Grouping(Expr):
    expression: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_grouping_expr(self)


@dataclass
class Literal(Expr):
    value: Any

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_literal_expr(self)


@dataclass
class Unary(Expr):
    operator: Token
    right: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_unary_expr(self)


@dataclass
class Variable(Expr):
    name: Token

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_variable_expr(self)


# --- Concrete Statement Nodes ---

@dataclass
class Expression(Stmt):
    expression: Expr

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_expression_stmt(self)


@dataclass
class Var(Stmt):
    name: Token
    initializer: Optional[Expr]

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_var_stmt(self)
