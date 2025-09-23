from llvmlite import ir, binding
from . import ast_nodes as ast
from .tokens import TokenType

class LLVMBackend(ast.StmtVisitor, ast.ExprVisitor):
    def __init__(self):
        self.binding = binding
        self.binding.initialize_native_target()
        self.binding.initialize_native_asmprinter()
        self.module = ir.Module(name="orion_module")
        self.builder = None
        self.named_values = {}

    def generate(self, statements: list[ast.Stmt]):
        for stmt in statements:
            stmt.accept(self)

    # --- Dummy implementations for all visitor methods ---
    def visit_grouping_expr(self, expr: 'Grouping'): pass
    def visit_unary_expr(self, expr: 'Unary'): pass
    def visit_variable_expr(self, expr: ast.Variable):
        ptr = self.named_values.get(expr.name.lexeme)
        if ptr:
            return self.builder.load(ptr, expr.name.lexeme)
        raise ValueError(f"Variable '{expr.name.lexeme}' not found")

    def visit_assign_expr(self, expr: ast.Assign):
        value = expr.value.accept(self)
        ptr = self.named_values.get(expr.name.lexeme)
        if ptr:
            self.builder.store(value, ptr)
            return value
        raise ValueError(f"Variable '{expr.name.lexeme}' not found")

    def visit_logical_expr(self, expr: 'Logical'): pass
    def visit_call_expr(self, expr: 'Call'): pass
    def visit_get_expr(self, expr: 'Get'): pass
    def visit_set_expr(self, expr: 'Set'): pass
    def visit_this_expr(self, expr: 'This'): pass
    def visit_list_literal_expr(self, expr: 'ListLiteral'): pass
    def visit_get_subscript_expr(self, expr: 'GetSubscript'): pass
    def visit_set_subscript_expr(self, expr: 'SetSubscript'): pass
    def visit_dict_literal_expr(self, expr: 'DictLiteral'): pass
    def visit_generic_type_expr(self, expr: 'GenericType'): pass
    def visit_expression_stmt(self, stmt: ast.Expression):
        stmt.expression.accept(self)
    def visit_var_stmt(self, stmt: ast.Var):
        name = stmt.name.lexeme
        initializer = stmt.initializer.accept(self) if stmt.initializer else None

        # Allocate memory for the variable
        ptr = self.builder.alloca(ir.IntType(32), name=name)
        self.named_values[name] = ptr

        if initializer:
            self.builder.store(initializer, ptr)
    def visit_binary_expr(self, expr: ast.Binary):
        left = expr.left.accept(self)
        right = expr.right.accept(self)

        if expr.operator.token_type == TokenType.PLUS:
            return self.builder.add(left, right, 'addtmp')
        elif expr.operator.token_type == TokenType.MINUS:
            return self.builder.sub(left, right, 'subtmp')
        elif expr.operator.token_type == TokenType.STAR:
            return self.builder.mul(left, right, 'multmp')
        elif expr.operator.token_type == TokenType.SLASH:
            return self.builder.sdiv(left, right, 'divtmp')

        # Comparison operators
        elif expr.operator.token_type == TokenType.EQUAL_EQUAL:
            return self.builder.icmp_signed('==', left, right, 'eetmp')
        elif expr.operator.token_type == TokenType.BANG_EQUAL:
            return self.builder.icmp_signed('!=', left, right, 'netmp')
        elif expr.operator.token_type == TokenType.LESS:
            return self.builder.icmp_signed('<', left, right, 'lttmp')
        elif expr.operator.token_type == TokenType.LESS_EQUAL:
            return self.builder.icmp_signed('<=', left, right, 'letmp')
        elif expr.operator.token_type == TokenType.GREATER:
            return self.builder.icmp_signed('>', left, right, 'gttmp')
        elif expr.operator.token_type == TokenType.GREATER_EQUAL:
            return self.builder.icmp_signed('>=', left, right, 'getmp')
        else:
            # Other binary operators not implemented yet
            return None

    def visit_block_stmt(self, stmt: ast.Block):
        for statement in stmt.statements:
            statement.accept(self)

    def visit_if_stmt(self, stmt: ast.If):
        condition = stmt.condition.accept(self)

        then_block = self.function.append_basic_block(name="then")

        if stmt.else_branch:
            else_block = self.function.append_basic_block(name="else")
            merge_block = self.function.append_basic_block(name="ifcont")
            self.builder.cbranch(condition, then_block, else_block)
        else:
            else_block = None
            merge_block = self.function.append_basic_block(name="ifcont")
            self.builder.cbranch(condition, then_block, merge_block)

        # Then block
        self.builder.position_at_start(then_block)
        stmt.then_branch.accept(self)
        if not then_block.is_terminated:
            self.builder.branch(merge_block)

        # Else block
        if stmt.else_branch:
            self.builder.position_at_start(else_block)
            stmt.else_branch.accept(self)
            if not else_block.is_terminated:
                self.builder.branch(merge_block)

        # If the merge block is empty at this point, it means all prior paths
        # terminated. We add an 'unreachable' instruction to make it a valid block.
        self.builder.position_at_start(merge_block)
        if not merge_block.instructions:
            self.builder.unreachable()

    def visit_while_stmt(self, stmt: ast.While):
        loop_header = self.function.append_basic_block(name="loop_header")
        loop_body = self.function.append_basic_block(name="loop_body")
        loop_exit = self.function.append_basic_block(name="loop_exit")

        self.builder.branch(loop_header)
        self.builder.position_at_start(loop_header)

        condition = stmt.condition.accept(self)
        self.builder.cbranch(condition, loop_body, loop_exit)

        self.builder.position_at_start(loop_body)
        stmt.body.accept(self)
        self.builder.branch(loop_header)

        self.builder.position_at_start(loop_exit)

    def visit_component_stmt(self, stmt: 'ComponentStmt'): pass
    def visit_style_prop_stmt(self, stmt: 'StyleProp'): pass
    def visit_state_block_stmt(self, stmt: 'StateBlock'): pass
    def visit_module_stmt(self, stmt: 'ModuleStmt'): pass
    def visit_use_stmt(self, stmt: 'UseStmt'): pass
    def visit_class_stmt(self, stmt: 'Class'): pass
    def visit_debug_stmt(self, stmt: 'Debug'): pass

    # --- Actual implementations ---
    def visit_function_stmt(self, stmt: ast.Function):
        func_name = stmt.name.lexeme
        func_type = ir.FunctionType(ir.IntType(32), [])
        self.function = ir.Function(self.module, func_type, name=func_name)
        block = self.function.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        for body_stmt in stmt.body:
            body_stmt.accept(self)

    def visit_return_stmt(self, stmt: ast.Return):
        if stmt.value:
            value = stmt.value.accept(self)
            self.builder.ret(value)
        else:
            self.builder.ret_void()

    def visit_literal_expr(self, expr: ast.Literal):
        if isinstance(expr.value, int):
            return ir.Constant(ir.IntType(32), expr.value)
        return None
