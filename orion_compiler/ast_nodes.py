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

    @abstractmethod
    def visit_assign_expr(self, expr: 'Assign'):
        raise NotImplementedError

    @abstractmethod
    def visit_logical_expr(self, expr: 'Logical'):
        raise NotImplementedError

    @abstractmethod
    def visit_call_expr(self, expr: 'Call'):
        raise NotImplementedError

    @abstractmethod
    def visit_get_expr(self, expr: 'Get'):
        raise NotImplementedError

    @abstractmethod
    def visit_set_expr(self, expr: 'Set'):
        raise NotImplementedError

    @abstractmethod
    def visit_this_expr(self, expr: 'This'):
        raise NotImplementedError

    @abstractmethod
    def visit_list_literal_expr(self, expr: 'ListLiteral'):
        raise NotImplementedError

    @abstractmethod
    def visit_get_subscript_expr(self, expr: 'GetSubscript'):
        raise NotImplementedError

    @abstractmethod
    def visit_set_subscript_expr(self, expr: 'SetSubscript'):
        raise NotImplementedError

    @abstractmethod
    def visit_dict_literal_expr(self, expr: 'DictLiteral'):
        raise NotImplementedError

    @abstractmethod
    def visit_generic_type_expr(self, expr: 'GenericType'):
        raise NotImplementedError


class StmtVisitor(ABC):
    @abstractmethod
    def visit_expression_stmt(self, stmt: 'Expression'):
        raise NotImplementedError

    @abstractmethod
    def visit_var_stmt(self, stmt: 'Var'):
        raise NotImplementedError

    @abstractmethod
    def visit_block_stmt(self, stmt: 'Block'):
        raise NotImplementedError

    @abstractmethod
    def visit_if_stmt(self, stmt: 'If'):
        raise NotImplementedError

    @abstractmethod
    def visit_while_stmt(self, stmt: 'While'):
        raise NotImplementedError

    @abstractmethod
    def visit_function_stmt(self, stmt: 'Function'):
        raise NotImplementedError

    @abstractmethod
    def visit_return_stmt(self, stmt: 'Return'):
        raise NotImplementedError

    @abstractmethod
    def visit_component_stmt(self, stmt: 'ComponentStmt'):
        raise NotImplementedError

    @abstractmethod
    def visit_style_prop_stmt(self, stmt: 'StyleProp'):
        raise NotImplementedError

    @abstractmethod
    def visit_state_block_stmt(self, stmt: 'StateBlock'):
        raise NotImplementedError

    @abstractmethod
    def visit_module_stmt(self, stmt: 'ModuleStmt'):
        raise NotImplementedError

    @abstractmethod
    def visit_use_stmt(self, stmt: 'UseStmt'):
        raise NotImplementedError

    @abstractmethod
    def visit_class_stmt(self, stmt: 'Class'):
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


@dataclass
class Assign(Expr):
    name: Token
    value: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_assign_expr(self)


@dataclass
class Logical(Expr):
    left: Expr
    operator: Token
    right: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_logical_expr(self)


@dataclass
class Call(Expr):
    callee: Expr
    paren: Token
    arguments: List[Expr]

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_call_expr(self)


@dataclass
class Get(Expr):
    object: Expr
    name: Token

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_get_expr(self)


@dataclass
class Set(Expr):
    object: Expr
    name: Token
    value: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_set_expr(self)


@dataclass
class This(Expr):
    keyword: Token

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_this_expr(self)


@dataclass
class ListLiteral(Expr):
    elements: List[Expr]

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_list_literal_expr(self)


@dataclass
class GetSubscript(Expr):
    object: Expr
    index: Expr
    bracket: Token

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_get_subscript_expr(self)


@dataclass
class SetSubscript(Expr):
    object: Expr
    index: Expr
    value: Expr
    bracket: Token

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_set_subscript_expr(self)


@dataclass
class DictLiteral(Expr):
    keys: List[Expr]
    values: List[Expr]

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_dict_literal_expr(self)


@dataclass
class GenericType(Expr):
    base_type: Expr
    type_parameters: List[Expr]

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_generic_type_expr(self)


# --- Concrete Statement Nodes ---

@dataclass
class Expression(Stmt):
    expression: Expr

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_expression_stmt(self)


@dataclass
class Var(Stmt):
    name: Token
    type_annotation: Optional[Expr]
    initializer: Optional[Expr]
    is_const: bool

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_var_stmt(self)


@dataclass
class Block(Stmt):
    statements: List[Stmt]

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_block_stmt(self)


@dataclass
class If(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Optional[Stmt]

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_if_stmt(self)


@dataclass
class While(Stmt):
    condition: Expr
    body: Stmt

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_while_stmt(self)


@dataclass
class Param:
    name: Token
    type_annotation: Optional[Expr]

@dataclass
class Function(Stmt):
    name: Token
    params: List[Param]
    body: List[Stmt]
    return_type: Optional[Expr]

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_function_stmt(self)


@dataclass
class Return(Stmt):
    keyword: Token
    value: Optional[Expr]

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_return_stmt(self)


# --- Component-related Statement Nodes ---

@dataclass
class StyleProp(Stmt):
    name: Token
    values: List[Token]

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_style_prop_stmt(self)


@dataclass
class StateBlock(Stmt):
    name: Token
    body: List[StyleProp]

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_state_block_stmt(self)


@dataclass
class ComponentStmt(Stmt):
    name: Token
    body: List[Stmt]

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_component_stmt(self)


@dataclass
class ModuleStmt(Stmt):
    name: Token

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_module_stmt(self)


@dataclass
class UseStmt(Stmt):
    name: Token
    alias: Optional[Token]

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_use_stmt(self)


@dataclass
class Class(Stmt):
    name: Token
    methods: List['Function']

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_class_stmt(self)
