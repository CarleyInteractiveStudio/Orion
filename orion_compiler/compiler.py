import ast_nodes as ast
from bytecode import Chunk, OpCode

class Compiler(ast.ExprVisitor, ast.StmtVisitor):
    """
    The Compiler walks the AST from the parser and emits bytecode.
    """
    def __init__(self):
        self.chunk = Chunk()
        self.had_error = False

    def compile(self, statements: list[ast.Stmt]) -> Chunk | None:
        for stmt in statements:
            self._compile_stmt(stmt)

        self._emit_return() # Finish the script with a return instruction.

        if self.had_error:
            return None
        return self.chunk

    def _compile_stmt(self, stmt: ast.Stmt):
        stmt.accept(self)

    def _compile_expr(self, expr: ast.Expr):
        expr.accept(self)

    # --- Emit Helpers ---

    def _current_chunk(self) -> Chunk:
        return self.chunk

    def _emit_byte(self, byte: int):
        # For now, we don't have line information from the AST nodes.
        # This should be added to the parser later.
        self._current_chunk().write(byte, 0)

    def _emit_bytes(self, byte1: int, byte2: int):
        self._emit_byte(byte1)
        self._emit_byte(byte2)

    def _emit_return(self):
        self._emit_byte(OpCode.OP_RETURN)

    def _make_constant(self, value) -> int:
        return self._current_chunk().add_constant(value)

    def _emit_constant(self, value):
        constant_idx = self._make_constant(value)
        if constant_idx > 255:
            # A real compiler would use multiple bytes for the operand.
            self.had_error = True
            print("Too many constants in one chunk.")
            return
        self._emit_bytes(OpCode.OP_CONSTANT, constant_idx)

    # --- Visitor Methods ---

    def visit_expression_stmt(self, stmt: ast.Expression):
        self._compile_expr(stmt.expression)
        self._emit_byte(OpCode.OP_POP)

    def visit_literal_expr(self, expr: ast.Literal):
        self._emit_constant(expr.value)

    def visit_grouping_expr(self, expr: ast.Grouping):
        self._compile_expr(expr.expression)

    def visit_unary_expr(self, expr: ast.Unary):
        self._compile_expr(expr.right)
        if expr.operator.token_type.name == 'MINUS':
            self._emit_byte(OpCode.OP_NEGATE)
        elif expr.operator.token_type.name == 'BANG': # '!' not in spec, but for completeness
            self._emit_byte(OpCode.OP_NOT)

    def visit_binary_expr(self, expr: ast.Binary):
        self._compile_expr(expr.left)
        self._compile_expr(expr.right)

        op_map = {
            'PLUS': OpCode.OP_ADD,
            'MINUS': OpCode.OP_SUBTRACT,
            'STAR': OpCode.OP_MULTIPLY,
            'SLASH': OpCode.OP_DIVIDE,
            'EQUAL_EQUAL': OpCode.OP_EQUAL,
            'GREATER': OpCode.OP_GREATER,
            'LESS': OpCode.OP_LESS,
            # Note: >= and <= would need to be implemented as two opcodes (e.g., NOT LESS)
        }

        op_code = op_map.get(expr.operator.token_type.name)
        if op_code:
            self._emit_byte(op_code)
        else:
            # Handle >= and <=, or other binary ops
            # For now, we ignore them. This is an incomplete implementation.
            pass

    # --- Other visitor methods will be added later ---
    # ...
    # For now, I will add placeholders to avoid abstract class errors.
    def visit_variable_expr(self, expr: ast.Variable): pass
    def visit_assign_expr(self, expr: ast.Assign): pass
    def visit_logical_expr(self, expr: ast.Logical): pass
    def visit_call_expr(self, expr: ast.Call): pass
    def visit_get_expr(self, expr: ast.Get): pass
    def visit_set_expr(self, expr: ast.Set): pass
    def visit_this_expr(self, expr: ast.This): pass
    def visit_var_stmt(self, stmt: ast.Var): pass
    def visit_block_stmt(self, stmt: ast.Block): pass
    def visit_if_stmt(self, stmt: ast.If): pass
    def visit_while_stmt(self, stmt: ast.While): pass
    def visit_function_stmt(self, stmt: ast.Function): pass
    def visit_return_stmt(self, stmt: ast.Return):
        if stmt.value:
            self._compile_expr(stmt.value)
            self._emit_byte(OpCode.OP_RETURN)
        else:
            self._emit_byte(OpCode.OP_NIL)
            self._emit_byte(OpCode.OP_RETURN)

    def visit_component_stmt(self, stmt: ast.ComponentStmt): pass
    def visit_style_prop_stmt(self, stmt: ast.StyleProp): pass
    def visit_state_block_stmt(self, stmt: ast.StateBlock): pass
    def visit_module_stmt(self, stmt: ast.ModuleStmt): pass
    def visit_use_stmt(self, stmt: ast.UseStmt): pass
