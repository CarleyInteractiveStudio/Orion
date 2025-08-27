from . import ast_nodes as ast
from .tokens import Token

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

    def visit_block_stmt(self, stmt: ast.Block) -> str:
        lines = ["(block"]
        for statement in stmt.statements:
            # This is a simple representation. A real pretty printer would handle indentation better.
            lines.append(f"  {statement.accept(self)}")
        lines.append(")")
        return "\n".join(lines)

    def visit_if_stmt(self, stmt: ast.If) -> str:
        parts = [
            "(if ",
            stmt.condition.accept(self),
            " ",
            stmt.then_branch.accept(self)
        ]
        if stmt.else_branch:
            parts.append(" else ")
            parts.append(stmt.else_branch.accept(self))
        parts.append(")")
        return "".join(parts)

    def visit_while_stmt(self, stmt: ast.While) -> str:
        parts = [
            "(while ",
            stmt.condition.accept(self),
            " ",
            stmt.body.accept(self),
            ")"
        ]
        return "".join(parts)

    def visit_function_stmt(self, stmt: ast.Function) -> str:
        param_str = ", ".join(p.lexeme for p in stmt.params)
        lines = [f"(fun {stmt.name.lexeme}({param_str}) {{"]
        for statement in stmt.body:
            lines.append(f"  {statement.accept(self)}")
        lines.append("})")
        return "\n".join(lines)

    def visit_return_stmt(self, stmt: ast.Return) -> str:
        if stmt.value:
            return self._parenthesize("return", stmt.value)
        return "(return)"

    def visit_module_stmt(self, stmt: ast.ModuleStmt) -> str:
        return f"(module {stmt.name.lexeme})"

    def visit_use_stmt(self, stmt: ast.UseStmt) -> str:
        if stmt.alias:
            return f"(use {stmt.name.lexeme} as {stmt.alias.lexeme})"
        return f"(use {stmt.name.lexeme})"

    # --- Component Visitor Methods ---

    def visit_component_stmt(self, stmt: ast.ComponentStmt) -> str:
        lines = [f"(component {stmt.name.lexeme} {{"]
        for s in stmt.body:
            lines.append(f"  {s.accept(self)}")
        lines.append("})")
        return "\n".join(lines)

    def visit_state_block_stmt(self, stmt: ast.StateBlock) -> str:
        lines = [f"  (state {stmt.name.lexeme} {{"]
        for s in stmt.body:
            lines.append(f"    {s.accept(self)}")
        lines.append("  })")
        return "\n".join(lines)

    def visit_style_prop_stmt(self, stmt: ast.StyleProp) -> str:
        value_str = " ".join(t.lexeme for t in stmt.values)
        return f"(style {stmt.name.lexeme}: {value_str})"

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

    def visit_assign_expr(self, expr: ast.Assign) -> str:
        return self._parenthesize(f"assign {expr.name.lexeme}", expr.value)

    def visit_logical_expr(self, expr: ast.Logical) -> str:
        return self._parenthesize(expr.operator.lexeme, expr.left, expr.right)

    def visit_call_expr(self, expr: ast.Call) -> str:
        return self._parenthesize("call", expr.callee, *expr.arguments)

    def visit_get_expr(self, expr: ast.Get) -> str:
        return self._parenthesize(f". {expr.name.lexeme}", expr.object)

    def visit_set_expr(self, expr: ast.Set) -> str:
        return self._parenthesize(f"= {expr.name.lexeme}", expr.object, expr.value)

    def visit_this_expr(self, expr: ast.This) -> str:
        return "this"

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
