import ast_nodes as ast
from tokens import Token

class AstPrinter(ast.ExprVisitor, ast.StmtVisitor):
    """
    A utility class to print the AST in a readable Lisp-like format.
    This is extremely useful for debugging the parser.
    """
    def print_program(self, statements: list[ast.Stmt]) -> str:
        lines = []
        for stmt in statements:
            lines.append(stmt.accept(self))
        return "\n".join(lines)

    # --- Statement Visitor Methods ---

    def visit_expression_stmt(self, stmt: ast.Expression) -> str:
        return self._parenthesize("expr_stmt", stmt.expression)

    def visit_var_stmt(self, stmt: ast.Var) -> str:
        if stmt.initializer:
            return self._parenthesize(f"var {stmt.name.lexeme}", stmt.initializer)
        return f"(var {stmt.name.lexeme})"

    # --- Expression Visitor Methods ---

    def visit_binary_expr(self, expr: ast.Binary) -> str:
        return self._parenthesize(expr.operator.lexeme, expr.left, expr.right)

    def visit_grouping_expr(self, expr: ast.Grouping) -> str:
        return self._parenthesize("group", expr.expression)

    def visit_literal_expr(self, expr: ast.Literal) -> str:
        if expr.value is None: return "nil"
        if isinstance(expr.value, str): return f'"{expr.value}"'
        if isinstance(expr.value, bool): return str(expr.value).lower()
        return str(expr.value)

    def visit_unary_expr(self, expr: ast.Unary) -> str:
        return self._parenthesize(expr.operator.lexeme, expr.right)

    def visit_variable_expr(self, expr: ast.Variable) -> str:
        return expr.name.lexeme

    # --- Helper Method ---

    def _parenthesize(self, name: str, *parts) -> str:
        """Helper to format a node and its children."""
        result = [f"({name}"]
        for part in parts:
            if isinstance(part, ast.Expr) or isinstance(part, ast.Stmt):
                result.append(f" {part.accept(self)}")
            else:
                # This case shouldn't be hit if used correctly
                result.append(f" {str(part)}")
        result.append(")")
        return "".join(result)
