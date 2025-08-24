from dataclasses import dataclass
import ast_nodes as ast
from bytecode import Chunk, OpCode
from tokens import Token
from objects import OrionCompiledFunction

def compile(statements: list[ast.Stmt]) -> OrionCompiledFunction | None:
    """Top-level compile function."""
    # The top level is treated like a function with no name or params.
    script_fn_node = ast.Function(Token(None, "<script>", None, 0), [], statements, None)
    compiler = Compiler(None, script_fn_node, "script")
    main_function = compiler._end_compiler()
    return None if compiler.had_error else main_function

@dataclass
class Local:
    name: Token
    depth: int

class Compiler(ast.ExprVisitor, ast.StmtVisitor):
    """
    The Compiler walks the AST from the parser and emits bytecode.
    Each instance handles a single function's compilation.
    """
    def __init__(self, enclosing, function_stmt: ast.Function, function_type: str):
        self.enclosing = enclosing
        self.type = function_type
        self.locals: list[Local] = []
        self.scope_depth: int = 0
        self.had_error = False

        func_name = function_stmt.name.lexeme if function_stmt.name else "<script>"
        self.function = OrionCompiledFunction(len(function_stmt.params), Chunk(), func_name)

        # The first stack slot is for the function itself.
        self._add_local(Token(None, "", None, 0))

        for param in function_stmt.params:
            self._add_local(param.name)

        # Compile the body
        self._compile_program(function_stmt.body)

    def _compile_program(self, statements: list[ast.Stmt]):
        for stmt in statements:
            self._compile_stmt(stmt)

    def _compile_stmt(self, stmt: ast.Stmt):
        stmt.accept(self)

    def _compile_expr(self, expr: ast.Expr):
        expr.accept(self)

    def _current_chunk(self) -> Chunk:
        return self.function.chunk

    def _emit_byte(self, byte: int):
        self._current_chunk().write(byte, 0)

    def _emit_bytes(self, byte1: int, byte2: int):
        self._emit_byte(byte1)
        self._emit_byte(byte2)

    def _emit_return(self):
        self._emit_byte(OpCode.OP_NIL)
        self._emit_byte(OpCode.OP_RETURN)

    def _end_compiler(self) -> OrionCompiledFunction:
        self._emit_return()
        return self.function

    def _make_constant(self, value) -> int:
        return self._current_chunk().add_constant(value)

    def _emit_constant(self, value):
        constant_idx = self._make_constant(value)
        if constant_idx > 255:
            self.had_error = True
            print("Too many constants in one chunk.")
            return
        self._emit_bytes(OpCode.OP_CONSTANT, constant_idx)

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
        elif expr.operator.token_type.name == 'BANG':
            self._emit_byte(OpCode.OP_NOT)

    def visit_binary_expr(self, expr: ast.Binary):
        self._compile_expr(expr.left)
        self._compile_expr(expr.right)
        op_map = {'PLUS': OpCode.OP_ADD, 'MINUS': OpCode.OP_SUBTRACT, 'STAR': OpCode.OP_MULTIPLY, 'SLASH': OpCode.OP_DIVIDE, 'EQUAL_EQUAL': OpCode.OP_EQUAL, 'GREATER': OpCode.OP_GREATER, 'LESS': OpCode.OP_LESS}
        self._emit_byte(op_map[expr.operator.token_type.name])

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

    def visit_var_stmt(self, stmt: ast.Var):
        self._compile_expr(stmt.initializer if stmt.initializer else ast.Literal(None))
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
        then_jump = self._emit_jump(OpCode.OP_JUMP_IF_FALSE)
        self._emit_byte(OpCode.OP_POP)
        self._compile_stmt(stmt.then_branch)
        else_jump = self._emit_jump(OpCode.OP_JUMP)
        self._patch_jump(then_jump)
        self._emit_byte(OpCode.OP_POP)
        if stmt.else_branch:
            self._compile_stmt(stmt.else_branch)
        self._patch_jump(else_jump)

    def visit_while_stmt(self, stmt: ast.While):
        loop_start = len(self._current_chunk().code)
        self._compile_expr(stmt.condition)
        exit_jump = self._emit_jump(OpCode.OP_JUMP_IF_FALSE)
        self._emit_byte(OpCode.OP_POP)
        self._compile_stmt(stmt.body)
        self._emit_loop(loop_start)
        self._patch_jump(exit_jump)
        self._emit_byte(OpCode.OP_POP)

    def visit_function_stmt(self, stmt: ast.Function):
        compiler = Compiler(self, stmt, "function")
        function_obj = compiler._end_compiler()
        constant_idx = self._make_constant(function_obj)
        self._emit_bytes(OpCode.OP_CONSTANT, constant_idx)
        if self.scope_depth > 0:
            self._add_local(stmt.name)
        else:
            self._emit_bytes(OpCode.OP_DEFINE_GLOBAL, self._make_constant(stmt.name.lexeme))

    def visit_call_expr(self, expr: ast.Call):
        self._compile_expr(expr.callee)
        for arg in expr.arguments:
            self._compile_expr(arg)
        self._emit_bytes(OpCode.OP_CALL, len(expr.arguments))

    def visit_return_stmt(self, stmt: ast.Return):
        if stmt.value:
            self._compile_expr(stmt.value)
            self._emit_byte(OpCode.OP_RETURN)
        else:
            self._emit_byte(OpCode.OP_NIL)
            self._emit_byte(OpCode.OP_RETURN)

    def _begin_scope(self): self.scope_depth += 1
    def _end_scope(self):
        self.scope_depth -= 1
        while self.locals and self.locals[-1].depth > self.scope_depth:
            self._emit_byte(OpCode.OP_POP)
            self.locals.pop()
    def _add_local(self, name: Token): self.locals.append(Local(name, self.scope_depth))
    def _resolve_local(self, name: Token) -> int:
        for i in range(len(self.locals) - 1, -1, -1):
            if name.lexeme == self.locals[i].name.lexeme:
                return i
        return -1
    def _emit_jump(self, instruction: OpCode) -> int:
        self._emit_byte(instruction)
        self._emit_byte(0xff); self._emit_byte(0xff)
        return len(self._current_chunk().code) - 2
    def _emit_loop(self, loop_start: int):
        self._emit_byte(OpCode.OP_LOOP)
        offset = len(self._current_chunk().code) - loop_start + 2
        if offset > 0xffff: self.had_error = True; print("Loop body too large.")
        self._emit_byte((offset >> 8) & 0xff); self._emit_byte(offset & 0xff)
    def _patch_jump(self, offset: int):
        jump = len(self._current_chunk().code) - offset - 2
        if jump > 0xffff: self.had_error = True; print("Too much code to jump over.")
        self._current_chunk().code[offset] = (jump >> 8) & 0xff
        self._current_chunk().code[offset + 1] = jump & 0xff

    # Placeholders for other features
    def visit_logical_expr(self, expr: ast.Logical): pass
    def visit_get_expr(self, expr: ast.Get):
        self._compile_expr(expr.object)
        self._emit_bytes(OpCode.OP_GET_PROPERTY, self._make_constant(expr.name.lexeme))

    def visit_set_expr(self, expr: ast.Set):
        self._compile_expr(expr.object)
        self._compile_expr(expr.value)
        self._emit_bytes(OpCode.OP_SET_PROPERTY, self._make_constant(expr.name.lexeme))

    def visit_this_expr(self, expr: ast.This): pass
    def visit_component_stmt(self, stmt: ast.ComponentStmt): pass
    def visit_style_prop_stmt(self, stmt: ast.StyleProp): pass
    def visit_state_block_stmt(self, stmt: ast.StateBlock): pass
    def visit_module_stmt(self, stmt: ast.ModuleStmt): pass
    def visit_use_stmt(self, stmt: ast.UseStmt):
        # The operand for OP_USE will be the constant index of the module name.
        self._emit_bytes(OpCode.OP_USE, self._make_constant(stmt.name.lexeme))

        # After OP_USE, the namespace object is on the stack.
        # Define it as a variable.
        bind_name = stmt.alias.lexeme if stmt.alias else stmt.name.lexeme

        # For now, modules can only be imported at the global scope.
        self._emit_bytes(OpCode.OP_DEFINE_GLOBAL, self._make_constant(bind_name))
