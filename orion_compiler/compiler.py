from dataclasses import dataclass
import ast_nodes as ast
from bytecode import Chunk, OpCode
from tokens import Token, TokenType
from objects import OrionCompiledFunction, OrionComponentDef
from orion_types import Type, ListType, DictType, ANY, NUMBER, STRING, BOOL, NIL, FUNCTION, MODULE, COMPONENT, ANY_LIST, ANY_DICT
from errors import type_error

def compile(statements: list[ast.Stmt]) -> OrionCompiledFunction | None:
    """Top-level compile function."""
    script_fn_node = ast.Function(Token(None, "<script>", None, 0), [], statements, None)

    analyzer = TypeAnalyzer()
    analyzer.analyze(statements)
    if analyzer.had_error:
        return None

    compiler = Compiler(None, script_fn_node, "script")
    main_function = compiler._end_compiler()
    return None if compiler.had_error else main_function

@dataclass
class Local:
    name: Token
    depth: int
    type: Type

class TypeAnalyzer(ast.ExprVisitor, ast.StmtVisitor):
    def __init__(self):
        self.locals: list[Local] = []
        self.globals: dict[str, Type] = {
            "clock": FUNCTION,
            "print": FUNCTION,
        }
        self.current_component: Optional[Type] = None
        self.component_props: dict[str, dict[str, Type]] = {}
        self.scope_depth: int = 0
        self.had_error = False
        self.type_map = {
            "any": ANY, "nil": NIL, "bool": BOOL, "number": NUMBER,
            "string": STRING, "function": FUNCTION, "component": COMPONENT,
            "module": MODULE, "list": ANY_LIST, "dict": ANY_DICT,
        }

    def analyze(self, statements: list[ast.Stmt]):
        for stmt in statements:
            self._analyze_stmt(stmt)

    def _analyze_stmt(self, stmt: ast.Stmt):
        stmt.accept(self)

    def _analyze_expr(self, expr: ast.Expr) -> Type:
        return expr.accept(self)

    def visit_var_stmt(self, stmt: ast.Var):
        declared_type = self._resolve_type_expr(stmt.type_annotation)

        if stmt.initializer:
            init_type = self._analyze_expr(stmt.initializer)
            if declared_type == ANY:
                declared_type = init_type

            if not self._is_assignable(declared_type, init_type):
                type_error(stmt.name, f"Initializer of type {init_type} cannot be assigned to variable of type {declared_type}.")
                self.had_error = True

        if self.scope_depth > 0:
            self._add_local(stmt.name, declared_type)
        else:
            self.globals[stmt.name.lexeme] = declared_type

    def visit_assign_expr(self, expr: ast.Assign) -> Type:
        value_type = self._analyze_expr(expr.value)
        var_type = self._get_var_type(expr.name)
        if not self._is_assignable(var_type, value_type):
            type_error(expr.name, f"Cannot assign value of type {value_type} to variable of type {var_type}.")
            self.had_error = True
        return value_type

    def visit_binary_expr(self, expr: ast.Binary) -> Type:
        left_type = self._analyze_expr(expr.left)
        right_type = self._analyze_expr(expr.right)
        op = expr.operator.token_type.name

        # Handle numeric operators
        if op in ('MINUS', 'STAR', 'SLASH', 'GREATER', 'LESS'):
            # If we know the types and they're wrong, error. Otherwise, assume it's okay.
            if left_type != ANY and right_type != ANY and (left_type != NUMBER or right_type != NUMBER):
                type_error(expr.operator, f"Operands for {op} must be numbers.")
                self.had_error = True
            # We can still infer the result type even if one operand is 'any'.
            return BOOL if op in ('GREATER', 'LESS') else NUMBER

        # Handle addition/concatenation
        if op == 'PLUS':
            if (left_type == NUMBER and right_type == NUMBER): return NUMBER
            if (left_type == STRING and right_type == STRING): return STRING
            # If one side is 'any', we can't know the result type.
            if left_type == ANY or right_type == ANY: return ANY
            # Otherwise, it's a definite error.
            type_error(expr.operator, "Operands for '+' must be two numbers or two strings.")
            self.had_error = True
            return ANY

        # Handle equality
        if op == 'EQUAL_EQUAL':
            # We can allow comparison between any two types.
            # The result is always a boolean.
            return BOOL

        return ANY

    def visit_unary_expr(self, expr: ast.Unary) -> Type:
        right_type = self._analyze_expr(expr.right)
        op = expr.operator.token_type.name
        if op == 'MINUS':
            if right_type != NUMBER:
                type_error(expr.operator, "Operand for '-' must be a number.")
                self.had_error = True
            return NUMBER
        if op == 'BANG':
            if right_type != BOOL:
                type_error(expr.operator, "Operand for '!' must be a boolean.")
                self.had_error = True
            return BOOL
        return ANY

    def visit_if_stmt(self, stmt: ast.If):
        condition_type = self._analyze_expr(stmt.condition)
        if condition_type != BOOL:
            type_error(self._get_token_from_expr(stmt.condition), f"If condition must be a boolean, but got {condition_type}.")
            self.had_error = True
        self._analyze_stmt(stmt.then_branch)
        if stmt.else_branch: self._analyze_stmt(stmt.else_branch)

    def visit_while_stmt(self, stmt: ast.While):
        condition_type = self._analyze_expr(stmt.condition)
        if condition_type != BOOL:
            type_error(self._get_token_from_expr(stmt.condition), f"While condition must be a boolean, but got {condition_type}.")
            self.had_error = True
        self._analyze_stmt(stmt.body)

    def visit_block_stmt(self, stmt: ast.Block):
        self._begin_scope()
        self.analyze(stmt.statements)
        self._end_scope()

    def visit_expression_stmt(self, stmt: ast.Expression): self._analyze_expr(stmt.expression)
    def visit_literal_expr(self, expr: ast.Literal) -> Type:
        if isinstance(expr.value, bool): return BOOL
        if isinstance(expr.value, (int, float)): return NUMBER
        if isinstance(expr.value, str): return STRING
        if expr.value is None: return NIL
        return ANY

    def visit_grouping_expr(self, expr: ast.Grouping) -> Type: return self._analyze_expr(expr.expression)
    def visit_variable_expr(self, expr: ast.Variable) -> Type: return self._get_var_type(expr.name)
    def visit_generic_type_expr(self, expr: ast.GenericType) -> Type: return ANY

    def _get_token_from_expr(self, expr: ast.Expr) -> Token:
        if isinstance(expr, (ast.Binary, ast.Unary)): return expr.operator
        if isinstance(expr, ast.Variable): return expr.name
        if isinstance(expr, ast.Literal): return Token(None, str(expr.value), None, 0)
        if isinstance(expr, (ast.GetSubscript, ast.SetSubscript)): return expr.bracket
        return Token(None, "expression", None, 0)

    def _begin_scope(self): self.scope_depth += 1
    def _end_scope(self):
        self.scope_depth -= 1
        while self.locals and self.locals[-1].depth > self.scope_depth:
            self.locals.pop()
    def _add_local(self, name: Token, type: Type): self.locals.append(Local(name, self.scope_depth, type))

    def _resolve_type_expr(self, type_expr: ast.Expr | None) -> Type:
        if type_expr is None: return ANY
        if isinstance(type_expr, ast.Variable):
            return self.type_map.get(type_expr.name.lexeme, ANY)
        if isinstance(type_expr, ast.GenericType):
            base_type_name = type_expr.base_type.name.lexeme

            params = [self._resolve_type_expr(p) for p in type_expr.type_parameters]

            if base_type_name == "list":
                if len(params) != 1:
                    print("Type Error: List type expects 1 type parameter.")
                    self.had_error = True
                    return ANY_LIST
                return ListType(params[0])
            elif base_type_name == "dict":
                if len(params) != 2:
                    print("Type Error: Dict type expects 2 type parameters (key, value).")
                    self.had_error = True
                    return ANY_DICT
                return DictType(params[0], params[1])
            else:
                print(f"Type Error: Type '{base_type_name}' is not generic.")
                self.had_error = True
                return ANY
        return ANY

    def _get_var_type(self, name: Token) -> Type:
        for local in reversed(self.locals):
            if name.lexeme == local.name.lexeme:
                return local.type
        if name.lexeme in self.globals:
            return self.globals[name.lexeme]
        type_error(name, f"Undeclared variable '{name.lexeme}'.")
        self.had_error = True
        return ANY

    def _is_assignable(self, target: Type, value: Type) -> bool:
        if target == value: return True
        if target == ANY: return True
        if value == ANY: return False

        if isinstance(target, ListType) and isinstance(value, ListType):
            return self._is_assignable(target.element_type, value.element_type)

        if isinstance(target, DictType) and isinstance(value, DictType):
            if value.key_type == ANY and value.value_type == ANY:
                return True
            key_match = self._is_assignable(target.key_type, value.key_type)
            value_match = self._is_assignable(target.value_type, value.value_type)
            return key_match and value_match

        return False

    def visit_function_stmt(self, stmt: ast.Function):
        # Declare the function name first to allow for recursion.
        # We don't have full FunctionType analysis yet, so use the generic type.
        if self.scope_depth > 0:
            self._add_local(stmt.name, FUNCTION)
        else:
            self.globals[stmt.name.lexeme] = FUNCTION

        # Analyze the function body in a new scope.
        self._begin_scope()
        for param in stmt.params:
            # Parameters are not typed yet, so treat as ANY.
            self._add_local(param.name, ANY)

        self.analyze(stmt.body)
        self._end_scope()

    def visit_return_stmt(self, stmt: ast.Return):
        if stmt.value: self._analyze_expr(stmt.value)

    def visit_call_expr(self, expr: ast.Call) -> Type:
        from orion_types import ComponentType, TYPE
        callee_type = self._analyze_expr(expr.callee)

        # Handle component instantiation calls, e.g., Button()
        if callee_type == TYPE and isinstance(expr.callee, ast.Variable):
            component_name = expr.callee.name.lexeme
            # The type of the *instance* is the ComponentType we registered
            if component_name in self.type_map and isinstance(self.type_map[component_name], ComponentType):
                # TODO: Check arguments match a constructor definition later
                return self.type_map[component_name]

        # Handle calls to methods or functions
        if callee_type == FUNCTION:
            # We don't analyze return types yet, so assume ANY.
            return ANY

        return ANY

    def visit_logical_expr(self, expr: ast.Logical) -> Type: return BOOL
    def visit_get_expr(self, expr: ast.Get) -> Type:
        object_type = self._analyze_expr(expr.object)
        from orion_types import ComponentType

        if isinstance(object_type, ListType):
            if expr.name.lexeme == "length":
                return NUMBER
            type_error(expr.name, f"Type 'list' has no property '{expr.name.lexeme}'.")
            self.had_error = True
            return ANY

        if isinstance(object_type, ComponentType):
            component_name = object_type.name
            prop_name = expr.name.lexeme
            if component_name in self.component_props and prop_name in self.component_props[component_name]:
                return self.component_props[component_name][prop_name]

            type_error(expr.name, f"Component '{component_name}' has no property named '{prop_name}'.")
            self.had_error = True
            return ANY

        if object_type == MODULE:
            return ANY

        if object_type != ANY:
            type_error(expr.name, f"Only components, lists, and modules have properties, not type '{object_type}'.")
            self.had_error = True
        return ANY

    def visit_set_expr(self, expr: ast.Set) -> Type:
        object_type = self._analyze_expr(expr.object)
        value_type = self._analyze_expr(expr.value)
        from orion_types import ComponentType

        if isinstance(object_type, ListType):
            type_error(expr.name, "Cannot set properties on a list.")
            self.had_error = True
            return value_type

        if isinstance(object_type, ComponentType):
            component_name = object_type.name
            prop_name = expr.name.lexeme
            if component_name in self.component_props and prop_name in self.component_props[component_name]:
                expected_type = self.component_props[component_name][prop_name]
                if not self._is_assignable(expected_type, value_type):
                    type_error(expr.name, f"Cannot assign value of type {value_type} to property '{prop_name}' of type {expected_type}.")
                    self.had_error = True
            else:
                type_error(expr.name, f"Component '{component_name}' has no property named '{prop_name}'.")
                self.had_error = True
            return value_type

        if object_type != ANY:
            type_error(expr.name, f"Only components have settable properties, not type '{object_type}'.")
            self.had_error = True
        return value_type

    def visit_this_expr(self, expr: ast.This) -> Type:
        if self.current_component is None:
            type_error(expr.keyword, "Cannot use 'this' outside of a component method.")
            self.had_error = True
            return ANY
        return self.current_component

    def visit_component_stmt(self, stmt: ast.ComponentStmt):
        from orion_types import ComponentType, TYPE
        component_name = stmt.name.lexeme

        new_component_type = ComponentType(component_name)
        self.type_map[component_name] = new_component_type
        self.globals[component_name] = TYPE

        original_component = self.current_component
        self.current_component = new_component_type

        # First pass: Gather properties so they are known before methods are analyzed.
        props: dict[str, Type] = {}
        for member in stmt.body:
            if isinstance(member, ast.StyleProp):
                prop_name = member.name.lexeme
                props[prop_name] = self._infer_type_from_style_prop(member)
        self.component_props[component_name] = props

        # Second pass: Analyze methods, which can now resolve properties on 'this'.
        for member in stmt.body:
            if isinstance(member, ast.Function):
                # Register the method so it can be found during type checking.
                props[member.name.lexeme] = FUNCTION
                self.visit_function_stmt(member)

        self.current_component = original_component

    def visit_style_prop_stmt(self, stmt: ast.StyleProp): pass
    def visit_state_block_stmt(self, stmt: ast.StateBlock): pass
    def visit_module_stmt(self, stmt: ast.ModuleStmt): pass
    def visit_use_stmt(self, stmt: ast.UseStmt):
        module_name = stmt.alias.lexeme if stmt.alias else stmt.name.lexeme
        self.globals[module_name] = MODULE
    def visit_list_literal_expr(self, expr: ast.ListLiteral) -> Type:
        if not expr.elements:
            return ListType(ANY)
        element_types = [self._analyze_expr(e) for e in expr.elements]
        first_type = element_types[0]
        if all(self._is_assignable(first_type, t) for t in element_types):
            return ListType(first_type)
        else:
            return ListType(ANY)

    def visit_dict_literal_expr(self, expr: ast.DictLiteral) -> Type:
        if not expr.keys:
            return DictType(ANY, ANY)
        key_types = [self._analyze_expr(k) for k in expr.keys]
        value_types = [self._analyze_expr(v) for v in expr.values]
        for key_type in key_types:
            if key_type not in (STRING, ANY):
                print("Type Error: Dictionary keys must be strings.")
                self.had_error = True
        first_value_type = value_types[0]
        if all(self._is_assignable(first_value_type, t) for t in value_types):
            return DictType(STRING, first_value_type)
        else:
            return DictType(STRING, ANY)

    def visit_get_subscript_expr(self, expr: ast.GetSubscript) -> Type:
        object_type = self._analyze_expr(expr.object)
        index_type = self._analyze_expr(expr.index)
        if isinstance(object_type, ListType):
            if not self._is_assignable(NUMBER, index_type):
                type_error(expr.bracket, f"List index must be a number, not type {index_type}.")
                self.had_error = True
            return object_type.element_type
        elif isinstance(object_type, DictType):
            if not self._is_assignable(object_type.key_type, index_type):
                type_error(expr.bracket, f"Key of type {index_type} cannot be used to index a dict with key type {object_type.key_type}.")
                self.had_error = True
            return object_type.value_type
        elif object_type != ANY:
            type_error(expr.bracket, f"Object of type {object_type} is not subscriptable.")
            self.had_error = True
        return ANY

    def visit_set_subscript_expr(self, expr: ast.SetSubscript) -> Type:
        object_type = self._analyze_expr(expr.object)
        index_type = self._analyze_expr(expr.index)
        value_type = self._analyze_expr(expr.value)
        if isinstance(object_type, ListType):
            if not self._is_assignable(NUMBER, index_type):
                type_error(expr.bracket, f"List index must be a number, not type {index_type}.")
                self.had_error = True
            if not self._is_assignable(object_type.element_type, value_type):
                type_error(expr.bracket, f"Cannot assign value of type {value_type} to a list of type {object_type}.")
                self.had_error = True
        elif isinstance(object_type, DictType):
            if not self._is_assignable(object_type.key_type, index_type):
                type_error(expr.bracket, f"Key of type {index_type} cannot be used to index a dict with key type {object_type.key_type}.")
                self.had_error = True
            if not self._is_assignable(object_type.value_type, value_type):
                type_error(expr.bracket, f"Cannot assign value of type {value_type} to a dict of type {object_type}.")
                self.had_error = True
        elif object_type != ANY:
            type_error(expr.bracket, f"Object of type {object_type} is not subscriptable.")
            self.had_error = True
        return value_type

    def _infer_type_from_style_prop(self, prop: ast.StyleProp) -> Type:
        if not prop.values:
            return NIL

        # Simple case: single literal value
        if len(prop.values) == 1:
            token = prop.values[0]
            if token.token_type == TokenType.NUMBER: return NUMBER
            if token.token_type == TokenType.STRING: return STRING
            if token.token_type in (TokenType.TRUE, TokenType.FALSE): return BOOL

        # For now, complex values (e.g., font: "Arial" 12) or variables are not type-checked for properties.
        return ANY

class Compiler(ast.ExprVisitor, ast.StmtVisitor):
    def __init__(self, enclosing, function_stmt: ast.Function, function_type: str):
        self.enclosing = enclosing
        self.type = function_type
        self.locals: list[Local] = []
        self.scope_depth: int = 0
        self.had_error = False
        func_name = function_stmt.name.lexeme if function_stmt.name else "<script>"
        self.function = OrionCompiledFunction(len(function_stmt.params), Chunk(), func_name)

        # In a method, slot 0 is reserved for the instance ('this').
        # In a function, it's an empty name for the function itself.
        if self.type == "method":
            self._add_local(Token(None, "this", None, 0), ANY)
        else:
            self._add_local(Token(None, "", None, 0), FUNCTION)

        for param in function_stmt.params:
            self._add_local(param.name, ANY)
        self._compile_program(function_stmt.body)
    def _compile_program(self, statements: list[ast.Stmt]):
        for stmt in statements: self._compile_stmt(stmt)
    def _compile_stmt(self, stmt: ast.Stmt): stmt.accept(self)
    def _compile_expr(self, expr: ast.Expr): expr.accept(self)
    def _current_chunk(self) -> Chunk: return self.function.chunk
    def _emit_byte(self, byte: int): self._current_chunk().write(byte, 0)
    def _emit_bytes(self, byte1: int, byte2: int):
        self._emit_byte(byte1)
        self._emit_byte(byte2)
    def _emit_return(self):
        self._emit_byte(OpCode.OP_NIL)
        self._emit_byte(OpCode.OP_RETURN)
    def _end_compiler(self) -> OrionCompiledFunction:
        self._emit_return()
        return self.function
    def _make_constant(self, value) -> int: return self._current_chunk().add_constant(value)
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
    def visit_literal_expr(self, expr: ast.Literal): self._emit_constant(expr.value)
    def visit_grouping_expr(self, expr: ast.Grouping): self._compile_expr(expr.expression)
    def visit_unary_expr(self, expr: ast.Unary):
        self._compile_expr(expr.right)
        if expr.operator.token_type.name == 'MINUS': self._emit_byte(OpCode.OP_NEGATE)
        elif expr.operator.token_type.name == 'BANG': self._emit_byte(OpCode.OP_NOT)
    def visit_binary_expr(self, expr: ast.Binary):
        self._compile_expr(expr.left)
        self._compile_expr(expr.right)
        op_map = {'PLUS': OpCode.OP_ADD, 'MINUS': OpCode.OP_SUBTRACT, 'STAR': OpCode.OP_MULTIPLY, 'SLASH': OpCode.OP_DIVIDE, 'EQUAL_EQUAL': OpCode.OP_EQUAL, 'GREATER': OpCode.OP_GREATER, 'LESS': OpCode.OP_LESS}
        self._emit_byte(op_map[expr.operator.token_type.name])
    def visit_variable_expr(self, expr: ast.Variable):
        arg = self._resolve_local(expr.name)
        if arg != -1: self._emit_bytes(OpCode.OP_GET_LOCAL, arg)
        else: self._emit_bytes(OpCode.OP_GET_GLOBAL, self._make_constant(expr.name.lexeme))
    def visit_assign_expr(self, expr: ast.Assign):
        self._compile_expr(expr.value)
        arg = self._resolve_local(expr.name)
        if arg != -1: self._emit_bytes(OpCode.OP_SET_LOCAL, arg)
        else: self._emit_bytes(OpCode.OP_SET_GLOBAL, self._make_constant(expr.name.lexeme))
    def visit_var_stmt(self, stmt: ast.Var):
        self._compile_expr(stmt.initializer if stmt.initializer else ast.Literal(None))
        if self.scope_depth > 0:
            self._add_local(stmt.name, ANY)
            return
        self._emit_bytes(OpCode.OP_DEFINE_GLOBAL, self._make_constant(stmt.name.lexeme))
    def visit_block_stmt(self, stmt: ast.Block):
        self._begin_scope()
        for statement in stmt.statements: self._compile_stmt(statement)
        self._end_scope()
    def visit_if_stmt(self, stmt: ast.If):
        self._compile_expr(stmt.condition)
        then_jump = self._emit_jump(OpCode.OP_JUMP_IF_FALSE)
        self._emit_byte(OpCode.OP_POP)
        self._compile_stmt(stmt.then_branch)
        else_jump = self._emit_jump(OpCode.OP_JUMP)
        self._patch_jump(then_jump)
        self._emit_byte(OpCode.OP_POP)
        if stmt.else_branch: self._compile_stmt(stmt.else_branch)
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
        if self.scope_depth > 0: self._add_local(stmt.name, FUNCTION)
        else: self._emit_bytes(OpCode.OP_DEFINE_GLOBAL, self._make_constant(stmt.name.lexeme))
    def visit_call_expr(self, expr: ast.Call):
        self._compile_expr(expr.callee)
        for arg in expr.arguments: self._compile_expr(arg)
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
    def _add_local(self, name: Token, type: Type): self.locals.append(Local(name, self.scope_depth, type))
    def _resolve_local(self, name: Token) -> int:
        for i in range(len(self.locals) - 1, -1, -1):
            if name.lexeme == self.locals[i].name.lexeme: return i
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
    def visit_this_expr(self, expr: ast.This):
        if self.type != 'method':
            # This should be caught by the TypeAnalyzer, but as a safeguard.
            print("Compile Error: Cannot use 'this' outside of a method.")
            self.had_error = True
            return

        # Resolve 'this' as a local variable. It's in slot 0 for methods.
        arg = self._resolve_local(expr.keyword)
        self._emit_bytes(OpCode.OP_GET_LOCAL, arg)

    def visit_component_stmt(self, stmt: ast.ComponentStmt):
        component_name = stmt.name.lexeme

        # Declare the class name as a global variable. It's temporarily nil.
        # This allows methods within the component to refer to the component's type.
        self._emit_bytes(OpCode.OP_DEFINE_GLOBAL, self._make_constant(component_name))

        # Create the definition object that will hold properties and methods.
        properties = [prop for prop in stmt.body if isinstance(prop, ast.StyleProp)]
        component_def = OrionComponentDef(component_name, properties)

        # Compile all function declarations inside the component as methods.
        for member in stmt.body:
            if isinstance(member, ast.Function):
                # The 'type' of a method compilation is 'method'
                compiler = Compiler(self, member, "method")
                function_obj = compiler._end_compiler()
                component_def.methods[member.name.lexeme] = function_obj

        # Now, push the fully-formed component definition object onto the stack
        # and update the global variable to point to it.
        self._emit_constant(component_def)
        self._emit_bytes(OpCode.OP_SET_GLOBAL, self._make_constant(component_name))

    def visit_style_prop_stmt(self, stmt: ast.StyleProp): pass
    def visit_state_block_stmt(self, stmt: ast.StateBlock): pass
    def visit_module_stmt(self, stmt: ast.ModuleStmt): pass
    def visit_use_stmt(self, stmt: ast.UseStmt):
        self._emit_bytes(OpCode.OP_USE, self._make_constant(stmt.name.lexeme))
        bind_name = stmt.alias.lexeme if stmt.alias else stmt.name.lexeme
        self._emit_bytes(OpCode.OP_DEFINE_GLOBAL, self._make_constant(bind_name))
    def visit_list_literal_expr(self, expr: ast.ListLiteral):
        for element in expr.elements: self._compile_expr(element)
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
    def visit_for_stmt(self, stmt: ast.Stmt): pass
    def visit_generic_type_expr(self, expr: ast.GenericType): pass
