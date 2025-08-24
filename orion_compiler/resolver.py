from typing import List, Dict, Optional

import ast_nodes as ast
from tokens import TokenType
# The resolver doesn't need the interpreter if it reports errors directly.
# This avoids a circular dependency.

class Resolver(ast.ExprVisitor, ast.StmtVisitor):
    """
    The Resolver performs static analysis to resolve all variables,
    ensuring they are declared before use and handling scopes correctly.
    """
    def __init__(self):
        # Each scope maps var name -> (is_defined: bool, type: Optional[str], is_const: bool)
        self.scopes: List[Dict[str, (bool, Optional[str], bool)]] = []
        self.had_error = False

    def resolve(self, statements: List[ast.Stmt]):
        self._begin_scope()
        for statement in statements:
            self._resolve_stmt(statement)
        self._end_scope()

    def _resolve_stmt(self, stmt: ast.Stmt):
        stmt.accept(self)

    def _resolve_expr(self, expr: ast.Expr):
        expr.accept(self)

    # --- Scope Management ---
    def _begin_scope(self):
        self.scopes.append({})

    def _end_scope(self):
        self.scopes.pop()

    def _declare(self, name: ast.Token):
        if not self.scopes: return
        scope = self.scopes[-1]
        if name.lexeme in scope:
            self._report_error(name, "Already a variable with this name in this scope.")
        scope[name.lexeme] = (False, None, False) # (defined, type, is_const)

    def _define(self, name: ast.Token, var_type: Optional[str] = None, is_const: bool = False):
        if not self.scopes: return
        self.scopes[-1][name.lexeme] = (True, var_type, is_const)

    def _resolve_local(self, name: ast.Token):
        for scope in reversed(self.scopes):
            if name.lexeme in scope:
                return

    def _get_var_type(self, name: ast.Token) -> Optional[str]:
        for scope in reversed(self.scopes):
            if name.lexeme in scope:
                return scope[name.lexeme][1]
        return None

    def _get_var_is_const(self, name: ast.Token) -> bool:
        for scope in reversed(self.scopes):
            if name.lexeme in scope:
                return scope[name.lexeme][2]
        return False

    def _type_of_expr(self, expr: ast.Expr) -> Optional[str]:
        # This is a simplified type inference system.
        if isinstance(expr, ast.Literal):
            # In a real type system, we'd have proper type objects.
            # For now, strings are fine.
            if isinstance(expr.value, (int, float)): return "float"
            if isinstance(expr.value, str): return "string"
            if isinstance(expr.value, bool): return "bool"
            return "any" # for nil etc.
        if isinstance(expr, ast.Variable):
            return self._get_var_type(expr.name)
        if isinstance(expr, ast.Binary):
            if expr.operator.token_type in [TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH]:
                return "float" # Assuming type check passes
            if expr.operator.token_type in [TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL, TokenType.EQUAL_EQUAL]:
                return "bool"
        if isinstance(expr, ast.Logical):
            return "bool"
        # Fallback for complex expressions like calls or gets.
        return "any"

    # --- Visitor Methods for Scope ---

    def visit_block_stmt(self, stmt: ast.Block):
        self._begin_scope()
        self.resolve(stmt.statements)
        self._end_scope()

    def visit_var_stmt(self, stmt: ast.Var):
        declared_type: Optional[str] = None
        if stmt.type_annotation:
            if isinstance(stmt.type_annotation, ast.Variable):
                declared_type = stmt.type_annotation.name.lexeme
            else:
                self._report_error(stmt.name, "Invalid type annotation.")

        self._declare(stmt.name)

        if stmt.initializer is not None:
            self._resolve_expr(stmt.initializer)
            initializer_type = self._type_of_expr(stmt.initializer)

            if declared_type and declared_type != initializer_type:
                self._report_error(stmt.name, f"Type mismatch: cannot assign value of type '{initializer_type}' to variable of type '{declared_type}'.")

            if not declared_type:
                declared_type = initializer_type

        self._define(stmt.name, declared_type, stmt.is_const)

    def visit_variable_expr(self, expr: ast.Variable):
        if self.scopes:
            var_state = self.scopes[-1].get(expr.name.lexeme)
            if var_state and var_state[0] is False:
                self._report_error(expr.name, "Can't read local variable in its own initializer.")
        self._resolve_local(expr.name)

    def visit_assign_expr(self, expr: ast.Assign):
        self._resolve_expr(expr.value)
        self._resolve_local(expr.name)

        # Check for const assignment
        is_const = self._get_var_is_const(expr.name)
        if is_const:
            self._report_error(expr.name, "Cannot assign to a constant variable.")

        # Type checking for assignment
        var_type = self._get_var_type(expr.name)
        value_type = self._type_of_expr(expr.value)

        if var_type and value_type and var_type != value_type:
            self._report_error(expr.name, f"Type mismatch: cannot assign value of type '{value_type}' to variable of type '{var_type}'.")

    def visit_function_stmt(self, stmt: ast.Function):
        self._declare(stmt.name)
        self._define(stmt.name)
        self._resolve_function(stmt)

    def _resolve_function(self, function: ast.Function):
        self._begin_scope()
        for param in function.params:
            self._declare(param)
            # Parameters are mutable by default.
            self._define(param, "any", is_const=False)
        self.resolve(function.body)
        self._end_scope()

    # --- Other Visitor Methods (Recursive Traversal) ---

    def visit_expression_stmt(self, stmt: ast.Expression): self._resolve_expr(stmt.expression)
    def visit_if_stmt(self, stmt: ast.If): self._resolve_expr(stmt.condition); self._resolve_stmt(stmt.then_branch);
    def visit_while_stmt(self, stmt: ast.While): self._resolve_expr(stmt.condition); self._resolve_stmt(stmt.body);
    def visit_return_stmt(self, stmt: ast.Return):
        if stmt.value: self._resolve_expr(stmt.value)
    def visit_binary_expr(self, expr: ast.Binary):
        self._resolve_expr(expr.left)
        self._resolve_expr(expr.right)

        left_type = self._type_of_expr(expr.left)
        right_type = self._type_of_expr(expr.right)

        op_type = expr.operator.token_type
        if op_type in [TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL]:
            if left_type not in ["float", "any"] or right_type not in ["float", "any"]:
                self._report_error(expr.operator, "Operands must be numbers.")

        if op_type == TokenType.PLUS:
            if not ((left_type in ["float", "any"] and right_type in ["float", "any"]) or \
                    (left_type in ["string", "any"] and right_type in ["string", "any"])):
                self._report_error(expr.operator, "Operands must be two numbers or two strings.")
    def visit_call_expr(self, expr: ast.Call): self._resolve_expr(expr.callee); [self._resolve_expr(arg) for arg in expr.arguments]
    def visit_get_expr(self, expr: ast.Get): self._resolve_expr(expr.object)
    def visit_grouping_expr(self, expr: ast.Grouping): self._resolve_expr(expr.expression)
    def visit_literal_expr(self, expr: ast.Literal): pass
    def visit_logical_expr(self, expr: ast.Logical): self._resolve_expr(expr.left); self._resolve_expr(expr.right)
    def visit_set_expr(self, expr: ast.Set): self._resolve_expr(expr.value); self._resolve_expr(expr.object)
    def visit_this_expr(self, expr: ast.This): pass
    def visit_unary_expr(self, expr: ast.Unary): self._resolve_expr(expr.right)
    def visit_component_stmt(self, stmt: ast.ComponentStmt): pass
    def visit_style_prop_stmt(self, stmt: ast.StyleProp): pass
    def visit_state_block_stmt(self, stmt: ast.StateBlock): pass
    def visit_module_stmt(self, stmt: ast.ModuleStmt): pass
    def visit_use_stmt(self, stmt: ast.UseStmt): pass

    def _report_error(self, token: ast.Token, message: str):
        self.had_error = True
        print(f"[Line {token.line}] ResolveError: {message}")
