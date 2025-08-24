from typing import List, Any

import ast_nodes as ast
from tokens import Token, TokenType
from errors import OrionRuntimeError
from environment import Environment

class Interpreter(ast.ExprVisitor, ast.StmtVisitor):
    """
    The Interpreter walks the AST and executes the code.
    """
    def __init__(self):
        self.environment = Environment()

    def interpret(self, statements: List[ast.Stmt]):
        """The main entry point for the interpreter."""
        try:
            for statement in statements:
                self._execute(statement)
        except OrionRuntimeError as error:
            # In a real compiler, this would be handled by a dedicated error reporter.
            print(f"[Line {error.token.line}] RuntimeError: {error.message}")

    def _execute(self, stmt: ast.Stmt):
        """Helper to execute a single statement."""
        stmt.accept(self)

    def _evaluate(self, expr: ast.Expr) -> Any:
        """Helper to evaluate a single expression."""
        return expr.accept(self)

    # --- STATEMENT VISITOR METHODS (SKELETON) ---

    def visit_expression_stmt(self, stmt: ast.Expression):
        self._evaluate(stmt.expression)
        return None

    def visit_var_stmt(self, stmt: ast.Var):
        value = None
        if stmt.initializer is not None:
            value = self._evaluate(stmt.initializer)

        self.environment.define(stmt.name.lexeme, value)
        return None

    # --- HELPER METHODS FOR RUNTIME CHECKS ---

    def _is_truthy(self, obj: Any) -> bool:
        """Defines what is 'true' in Orion. False and None are falsey."""
        if obj is None: return False
        if isinstance(obj, bool): return obj
        return True

    def _is_equal(self, a: Any, b: Any) -> bool:
        """Defines equality in Orion."""
        if a is None and b is None: return True
        if a is None: return False
        return a == b

    def _check_number_operand(self, operator: Token, operand: Any):
        if isinstance(operand, (int, float)): return
        raise OrionRuntimeError(operator, "Operand must be a number.")

    def _check_number_operands(self, operator: Token, left: Any, right: Any):
        if isinstance(left, (int, float)) and isinstance(right, (int, float)): return
        raise OrionRuntimeError(operator, "Operands must be numbers.")


    # --- EXPRESSION VISITOR METHODS ---

    def visit_binary_expr(self, expr: ast.Binary):
        left = self._evaluate(expr.left)
        right = self._evaluate(expr.right)
        op_type = expr.operator.token_type

        if op_type == TokenType.MINUS:
            self._check_number_operands(expr.operator, left, right)
            return float(left) - float(right)
        if op_type == TokenType.SLASH:
            self._check_number_operands(expr.operator, left, right)
            if float(right) == 0.0:
                raise OrionRuntimeError(expr.operator, "Division by zero.")
            return float(left) / float(right)
        if op_type == TokenType.STAR:
            self._check_number_operands(expr.operator, left, right)
            return float(left) * float(right)
        if op_type == TokenType.PLUS:
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return float(left) + float(right)
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            raise OrionRuntimeError(expr.operator, "Operands must be two numbers or two strings.")

        if op_type == TokenType.GREATER:
            self._check_number_operands(expr.operator, left, right)
            return float(left) > float(right)
        if op_type == TokenType.GREATER_EQUAL:
            self._check_number_operands(expr.operator, left, right)
            return float(left) >= float(right)
        if op_type == TokenType.LESS:
            self._check_number_operands(expr.operator, left, right)
            return float(left) < float(right)
        if op_type == TokenType.LESS_EQUAL:
            self._check_number_operands(expr.operator, left, right)
            return float(left) <= float(right)

        if op_type == TokenType.EQUAL_EQUAL:
            return self._is_equal(left, right)

        # Should be unreachable.
        return None

    def visit_grouping_expr(self, expr: ast.Grouping):
        return self._evaluate(expr.expression)

    def visit_literal_expr(self, expr: ast.Literal):
        return expr.value

    def visit_unary_expr(self, expr: ast.Unary):
        right = self._evaluate(expr.right)
        if expr.operator.token_type == TokenType.MINUS:
            self._check_number_operand(expr.operator, right)
            return -float(right)

        # Unreachable for now, but good for future extension with '!'
        return None

    def visit_variable_expr(self, expr: ast.Variable):
        return self.environment.get(expr.name)
