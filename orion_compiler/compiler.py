from dataclasses import dataclass
import ast_nodes as ast
from bytecode import Chunk, OpCode
from tokens import Token
from objects import OrionCompiledFunction
from orion_types import OrionType
from errors import type_error

def compile(statements: list[ast.Stmt]) -> OrionCompiledFunction | None:
    """Top-level compile function."""
    script_fn_node = ast.Function(Token(None, "<script>", None, 0), [], statements, None)

    # 1. Run Type Analysis first
    analyzer = TypeAnalyzer()
    analyzer.analyze(statements)
    if analyzer.had_error:
        return None

    # 2. If types are valid, compile to bytecode
    compiler = Compiler(None, script_fn_node, "script")
    main_function = compiler._end_compiler()
    return None if compiler.had_error else main_function

@dataclass
class Local:
    name: Token
    depth: int
    type: OrionType

# --- Static Type Analyzer ---

class TypeAnalyzer(ast.ExprVisitor, ast.StmtVisitor):
    def __init__(self):
        self.locals: list[Local] = []
        self.globals: dict[str, OrionType] = {}
        self.scope_depth: int = 0
        self.had_error = False
        self.type_map = {
            "any": OrionType.ANY, "nil": OrionType.NIL, "bool": OrionType.BOOL,
            "number": OrionType.NUMBER, "string": OrionType.STRING, "function": OrionType.FUNCTION,
            "component": OrionType.COMPONENT, "module": OrionType.MODULE, "list": OrionType.LIST,
        }

    def analyze(self, statements: list[ast.Stmt]):
        for stmt in statements:
            self._analyze_stmt(stmt)

    def _analyze_stmt(self, stmt: ast.Stmt):
        stmt.accept(self)

    def _analyze_expr(self, expr: ast.Expr) -> OrionType:
        return expr.accept(self)

    def visit_var_stmt(self, stmt: ast.Var):
        declared_type = self._resolve_type_expr(stmt.type_annotation)

        init_type = OrionType.ANY
        if stmt.initializer:
            init_type = self._analyze_expr(stmt.initializer)

        if declared_type == OrionType.ANY:
            declared_type = init_type

        if declared_type != OrionType.ANY and init_type != OrionType.ANY and declared_type != init_type:
            type_error(stmt.name, f"Initializer of type {init_type.name} cannot be assigned to variable of type {declared_type.name}.")
            self.had_error = True

        if self.scope_depth > 0:
            self._add_local(stmt.name, declared_type)
        else:
            self.globals[stmt.name.lexeme] = declared_type

    def visit_assign_expr(self, expr: ast.Assign) -> OrionType:
        value_type = self._analyze_expr(expr.value)
        var_type = self._get_var_type(expr.name)

        if var_type != OrionType.ANY and var_type != value_type:
            type_error(expr.name, f"Cannot assign value of type {value_type.name} to variable of type {var_type.name}.")
            self.had_error = True

        return value_type

    def visit_binary_expr(self, expr: ast.Binary) -> OrionType:
        left_type = self._analyze_expr(expr.left)
        right_type = self._analyze_expr(expr.right)
        op = expr.operator.token_type.name

        if left_type == OrionType.ANY or right_type == OrionType.ANY:
            return OrionType.ANY

        if op in ('MINUS', 'STAR', 'SLASH', 'GREATER', 'LESS'):
            if left_type != OrionType.NUMBER or right_type != OrionType.NUMBER:
                type_error(expr.operator, f"Operands for {op} must be numbers.")
                self.had_error = True
            return OrionType.NUMBER if op not in ('GREATER', 'LESS') else OrionType.BOOL

        if op == 'PLUS':
            if (left_type == OrionType.NUMBER and right_type == OrionType.NUMBER):
                return OrionType.NUMBER
            if (left_type == OrionType.STRING and right_type == OrionType.STRING):
                return OrionType.STRING
            type_error(expr.operator, "Operands for '+' must be two numbers or two strings.")
            self.had_error = True
            return OrionType.ANY

        if op == 'EQUAL_EQUAL':
            if left_type != right_type:
                type_error(expr.operator, f"Cannot compare values of type {left_type.name} and {right_type.name}.")
                self.had_error = True
            return OrionType.BOOL

        return OrionType.ANY

    def visit_unary_expr(self, expr: ast.Unary) -> OrionType:
        right_type = self._analyze_expr(expr.right)
        op = expr.operator.token_type.name

        if op == 'MINUS':
            if right_type != OrionType.NUMBER:
                type_error(expr.operator, "Operand for '-' must be a number.")
                self.had_error = True
            return OrionType.NUMBER

        if op == 'BANG':
            if right_type != OrionType.BOOL:
                type_error(expr.operator, "Operand for '!' must be a boolean.")
                self.had_error = True
            return OrionType.BOOL

        return OrionType.ANY

    def visit_if_stmt(self, stmt: ast.If):
        condition_type = self._analyze_expr(stmt.condition)
        if condition_type != OrionType.BOOL:
            token = self._get_token_from_expr(stmt.condition)
            type_error(token, f"If condition must be a boolean, but got {condition_type.name}.")
            self.had_error = True
        self._analyze_stmt(stmt.then_branch)
        if stmt.else_branch:
            self._analyze_stmt(stmt.else_branch)

    def visit_while_stmt(self, stmt: ast.While):
        condition_type = self._analyze_expr(stmt.condition)
        if condition_type != OrionType.BOOL:
            token = self._get_token_from_expr(stmt.condition)
            type_error(token, f"While condition must be a boolean, but got {condition_type.name}.")
            self.had_error = True
        self._analyze_stmt(stmt.body)

    def visit_block_stmt(self, stmt: ast.Block):
        self._begin_scope()
        self.analyze(stmt.statements)
        self._end_scope()

    def visit_expression_stmt(self, stmt: ast.Expression): self._analyze_expr(stmt.expression)
    def visit_literal_expr(self, expr: ast.Literal) -> OrionType:
        if isinstance(expr.value, bool): return OrionType.BOOL
        if isinstance(expr.value, (int, float)): return OrionType.NUMBER
        if isinstance(expr.value, str): return OrionType.STRING
        if expr.value is None: return OrionType.NIL
        return OrionType.ANY

    def visit_grouping_expr(self, expr: ast.Grouping) -> OrionType: return self._analyze_expr(expr.expression)
    def visit_variable_expr(self, expr: ast.Variable) -> OrionType: return self._get_var_type(expr.name)

    def _get_token_from_expr(self, expr: ast.Expr) -> Token:
        if isinstance(expr, (ast.Binary, ast.Unary)):
            return expr.operator
        if isinstance(expr, ast.Variable):
            return expr.name
        if isinstance(expr, ast.Literal):
            return Token(None, str(expr.value), None, 0)
        if isinstance(expr, (ast.GetSubscript, ast.SetSubscript)):
            return expr.bracket
        return Token(None, "expression", None, 0)

    def _begin_scope(self): self.scope_depth += 1
    def _end_scope(self):
        self.scope_depth -= 1
        while self.locals and self.locals[-1].depth > self.scope_depth:
            self.locals.pop()
    def _add_local(self, name: Token, type: OrionType): self.locals.append(Local(name, self.scope_depth, type))
    def _resolve_type_expr(self, type_expr: ast.Expr | None) -> OrionType:
        if type_expr is None: return OrionType.ANY
        if isinstance(type_expr, ast.Variable):
            return self.type_map.get(type_expr.name.lexeme, OrionType.ANY)
        return OrionType.ANY
    def _get_var_type(self, name: Token) -> OrionType:
        for local in reversed(self.locals):
            if name.lexeme == local.name.lexeme:
                return local.type
        return self.globals.get(name.lexeme, OrionType.ANY)

    def visit_function_stmt(self, stmt: ast.Function): pass # TODO
    def visit_return_stmt(self, stmt: ast.Return):
        if stmt.value:
            self._analyze_expr(stmt.value)
    def visit_call_expr(self, expr: ast.Call) -> OrionType: return OrionType.ANY # TODO
    def visit_logical_expr(self, expr: ast.Logical) -> OrionType: return OrionType.BOOL # Simple for now
    def visit_get_expr(self, expr: ast.Get) -> OrionType: return OrionType.ANY # TODO
    def visit_set_expr(self, expr: ast.Set) -> OrionType: return OrionType.ANY # TODO
    def visit_this_expr(self, expr: ast.This) -> OrionType: return OrionType.ANY # TODO
    def visit_component_stmt(self, stmt: ast.ComponentStmt): pass
    def visit_style_prop_stmt(self, stmt: ast.StyleProp): pass
    def visit_state_block_stmt(self, stmt: ast.StateBlock): pass
    def visit_module_stmt(self, stmt: ast.ModuleStmt): pass
    def visit_use_stmt(self, stmt: ast.UseStmt): pass
    def visit_list_literal_expr(self, expr: ast.ListLiteral) -> OrionType:
        for element in expr.elements:
            self._analyze_expr(element)
        return OrionType.LIST
    def visit_get_subscript_expr(self, expr: ast.GetSubscript) -> OrionType:
        object_type = self._analyze_expr(expr.object)
        index_type = self._analyze_expr(expr.index)

        if object_type == OrionType.LIST:
            if index_type not in (OrionType.NUMBER, OrionType.ANY):
                type_error(expr.bracket, f"List index must be a number, not type {index_type.name}.")
                self.had_error = True
        elif object_type == OrionType.DICT:
            if index_type not in (OrionType.STRING, OrionType.ANY):
                type_error(expr.bracket, f"Dictionary key must be a string, not type {index_type.name}.")
                self.had_error = True
        elif object_type != OrionType.ANY:
            type_error(expr.bracket, f"Object of type {object_type.name} is not subscriptable.")
            self.had_error = True

        return OrionType.ANY

    def visit_set_subscript_expr(self, expr: ast.SetSubscript) -> OrionType:
        object_type = self._analyze_expr(expr.object)
        index_type = self._analyze_expr(expr.index)
        value_type = self._analyze_expr(expr.value)

        if object_type == OrionType.LIST:
            if index_type not in (OrionType.NUMBER, OrionType.ANY):
                type_error(expr.bracket, f"List index must be a number, not type {index_type.name}.")
                self.had_error = True
        elif object_type == OrionType.DICT:
            if index_type not in (OrionType.STRING, OrionType.ANY):
                type_error(expr.bracket, f"Dictionary key must be a string, not type {index_type.name}.")
                self.had_error = True
        elif object_type != OrionType.ANY:
            type_error(expr.bracket, f"Object of type {object_type.name} is not subscriptable.")
            self.had_error = True

        return value_type

    def visit_dict_literal_expr(self, expr: ast.DictLiteral) -> OrionType:
        for i in range(len(expr.keys)):
            key_type = self._analyze_expr(expr.keys[i])
            if key_type not in (OrionType.STRING, OrionType.ANY):
                # This error reporting is tricky without a token for the key expression.
                # The parser already enforces string literals, so this is just for safety.
                print(f"Type Error: Dictionary keys must be strings.")
                self.had_error = True
            self._analyze_expr(expr.values[i])
        return OrionType.DICT

# --- Bytecode Compiler ---
class Compiler(ast.ExprVisitor, ast.StmtVisitor):
    def __init__(self, enclosing, function_stmt: ast.Function, function_type: str):
        self.enclosing = enclosing
        self.type = function_type
        self.locals: list[Local] = []
        self.scope_depth: int = 0
        self.had_error = False
        func_name = function_stmt.name.lexeme if function_stmt.name else "<script>"
        self.function = OrionCompiledFunction(len(function_stmt.params), Chunk(), func_name)
        self._add_local(Token(None, "", None, 0), OrionType.FUNCTION)
        for param in function_stmt.params:
            self._add_local(param.name, OrionType.ANY)
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
            self._add_local(stmt.name, OrionType.ANY)
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
            self._add_local(stmt.name, OrionType.FUNCTION)
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
    def _add_local(self, name: Token, type: OrionType): self.locals.append(Local(name, self.scope_depth, type))
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
        self._emit_bytes(OpCode.OP_USE, self._make_constant(stmt.name.lexeme))
        bind_name = stmt.alias.lexeme if stmt.alias else stmt.name.lexeme
        self._emit_bytes(OpCode.OP_DEFINE_GLOBAL, self._make_constant(bind_name))
    def visit_list_literal_expr(self, expr: ast.ListLiteral):
        for element in expr.elements:
            self._compile_expr(element)
        self._emit_bytes(OpCode.OP_BUILD_LIST, len(expr.elements))
    def visit_get_subscript_expr(self, expr: ast.GetSubscript):
        self._compile_expr(expr.object)
        self._compile_expr(expr.index)
        self._emit_byte(OpCode.OP_GET_SUBSCRIPT)
    def visit_set_subscript_expr(self, expr: ast.SetSubscript):
        self._compile_expr(expr.object)
        self._compile_expr(expr.index)
        self._compile_expr(expr.value)
        self._emit_byte(OpCode.OP_SET_SUBSCRIPT)
    def visit_dict_literal_expr(self, expr: ast.DictLiteral):
        for i in range(len(expr.keys)):
            self._compile_expr(expr.keys[i])
            self._compile_expr(expr.values[i])
        self._emit_bytes(OpCode.OP_BUILD_DICT, len(expr.keys))
