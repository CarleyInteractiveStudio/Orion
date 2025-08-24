from dataclasses import dataclass
import ast_nodes as ast
from bytecode import Chunk, OpCode
from tokens import Token

@dataclass
class Local:
    name: Token
    depth: int

class Compiler(ast.ExprVisitor, ast.StmtVisitor):
    """
    The Compiler walks the AST from the parser and emits bytecode.
    """
    def __init__(self):
        self.chunk = Chunk()
        self.locals: list[Local] = []
        self.scope_depth: int = 0
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
    def visit_variable_expr(self, expr: ast.Variable):
        arg = self._resolve_local(expr.name)
        if arg != -1:
            self._emit_bytes(OpCode.OP_GET_LOCAL, arg)
        else:
            self._emit_bytes(OpCode.OP_GET_GLOBAL, self._make_constant(expr.name.lexeme))

    def visit_assign_expr(self, expr: ast.Assign):
        self._compile_expr(expr.value)
        arg = self._resolve_local(expr.name)
        if arg != -1:
            self._emit_bytes(OpCode.OP_SET_LOCAL, arg)
        else:
            self._emit_bytes(OpCode.OP_SET_GLOBAL, self._make_constant(expr.name.lexeme))

    def visit_logical_expr(self, expr: ast.Logical): pass
    def visit_call_expr(self, expr: ast.Call): pass
    def visit_get_expr(self, expr: ast.Get): pass
    def visit_set_expr(self, expr: ast.Set): pass
    def visit_this_expr(self, expr: ast.This): pass
    def visit_var_stmt(self, stmt: ast.Var):
        self._compile_expr(stmt.initializer if stmt.initializer else ast.Literal(None))

        # For global variables, we define them by name.
        # For local variables, they are already on the stack.
        if self.scope_depth > 0:
            self._add_local(stmt.name)
            return

        self._emit_bytes(OpCode.OP_DEFINE_GLOBAL, self._make_constant(stmt.name.lexeme))

    def visit_block_stmt(self, stmt: ast.Block):
        self._begin_scope()
        for statement in stmt.statements:
            self._compile_stmt(statement)
        self._end_scope()
    def visit_if_stmt(self, stmt: ast.If):
        self._compile_expr(stmt.condition)

        # Emit a jump to skip the 'then' branch if the condition is false.
        then_jump = self._emit_jump(OpCode.OP_JUMP_IF_FALSE)

        self._emit_byte(OpCode.OP_POP) # Pop condition value
        self._compile_stmt(stmt.then_branch)

        # Emit a jump to skip the 'else' branch if the 'then' branch was taken.
        else_jump = self._emit_jump(OpCode.OP_JUMP)

        self._patch_jump(then_jump)
        self._emit_byte(OpCode.OP_POP) # Pop condition value

        if stmt.else_branch:
            self._compile_stmt(stmt.else_branch)

        self._patch_jump(else_jump)
    def visit_while_stmt(self, stmt: ast.While):
        loop_start = len(self._current_chunk().code)

        self._compile_expr(stmt.condition)

        exit_jump = self._emit_jump(OpCode.OP_JUMP_IF_FALSE)

        self._emit_byte(OpCode.OP_POP) # Pop condition
        self._compile_stmt(stmt.body)
        self._emit_loop(loop_start)

        self._patch_jump(exit_jump)
        self._emit_byte(OpCode.OP_POP) # Pop condition to exit loop

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

    # --- Scope and Local Variable Helpers ---

    def _begin_scope(self):
        self.scope_depth += 1

    def _end_scope(self):
        self.scope_depth -= 1

        # Pop local variables from the stack when the scope ends
        while self.locals and self.locals[-1].depth > self.scope_depth:
            self._emit_byte(OpCode.OP_POP)
            self.locals.pop()

    def _add_local(self, name: Token):
        # A real compiler would check for redeclaration here.
        self.locals.append(Local(name, self.scope_depth))

    def _emit_jump(self, instruction: OpCode) -> int:
        """Emits a jump instruction with a placeholder offset and returns its location."""
        self._emit_byte(instruction)
        # Emit two bytes for the placeholder offset
        self._emit_byte(0xff)
        self._emit_byte(0xff)
        return len(self._current_chunk().code) - 2

    def _emit_loop(self, loop_start: int):
        self._emit_byte(OpCode.OP_LOOP)

        offset = len(self._current_chunk().code) - loop_start + 2
        if offset > 0xffff:
            self.had_error = True
            print("Loop body too large.")

        self._emit_byte((offset >> 8) & 0xff)
        self._emit_byte(offset & 0xff)

    def _patch_jump(self, offset: int):
        """Goes back and fills in the correct jump offset."""
        # -2 to account for the size of the jump offset itself.
        jump = len(self._current_chunk().code) - offset - 2

        if jump > 0xffff: # 16-bit offset
            self.had_error = True
            print("Too much code to jump over.")

        # Write the 16-bit jump offset
        self._current_chunk().code[offset] = (jump >> 8) & 0xff
        self._current_chunk().code[offset + 1] = jump & 0xff

    def _resolve_local(self, name: Token) -> int:
        """
        Finds a local variable in the compiler's scope stack.
        Returns the stack slot index, or -1 if not found.
        """
        for i in range(len(self.locals) - 1, -1, -1):
            local = self.locals[i]
            if name.lexeme == local.name.lexeme:
                # A real compiler would check if the var was initialized here.
                return i
        return -1
