from typing import List, Any

import ast_nodes as ast
from tokens import Token, TokenType
from errors import OrionRuntimeError, Return
from environment import Environment
from callables import OrionFunction, OrionCallable, OrionComponent, OrionInstance

class Interpreter(ast.ExprVisitor, ast.StmtVisitor):
    """
    The Interpreter walks the AST and executes the code.
    """
    def __init__(self):
        self.environment = Environment()

    def interpret(self, statements: List[ast.Stmt]) -> Environment:
        """The main entry point for the interpreter."""
        try:
            for statement in statements:
                self._execute(statement)
        except OrionRuntimeError as error:
            # In a real compiler, this would be handled by a dedicated error reporter.
            print(f"[Line {error.token.line}] RuntimeError: {error.message}")

        return self.environment

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

    def visit_block_stmt(self, stmt: ast.Block):
        self._execute_block(stmt.statements, Environment(self.environment))
        return None

    def visit_if_stmt(self, stmt: ast.If):
        if self._is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.then_branch)
        elif stmt.else_branch is not None:
            self._execute(stmt.else_branch)
        return None

    def visit_while_stmt(self, stmt: ast.While):
        while self._is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.body)
        return None

    def visit_function_stmt(self, stmt: ast.Function):
        function = OrionFunction(stmt, self.environment)
        self.environment.define(stmt.name.lexeme, function)
        return None

    def visit_return_stmt(self, stmt: ast.Return):
        value = None
        if stmt.value is not None:
            value = self._evaluate(stmt.value)

        raise Return(value)

    def visit_module_stmt(self, stmt: ast.ModuleStmt):
        # For now, module declarations don't have a runtime behavior.
        # A static analyzer might use this, or a build system.
        return None

    def visit_use_stmt(self, stmt: ast.UseStmt):
        module_name = stmt.name.lexeme
        # Assume modules are relative to the compiler directory for now.
        file_path = f"orion_compiler/{module_name}.orion"

        # This import is here to avoid a top-level circular dependency
        from orion import Orion

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
        except FileNotFoundError:
            raise OrionRuntimeError(stmt.name, f"Module file not found: '{file_path}'")

        # Run the module code in a new, separate execution pipeline
        module_runner = Orion()
        module_environment = module_runner.run(source)

        # Create a namespace instance to hold the module's exports
        namespace = OrionInstance()
        namespace.fields = module_environment.values

        # Bind the namespace object to a variable in the current environment
        bind_name = stmt.alias.lexeme if stmt.alias else module_name
        self.environment.define(bind_name, namespace)
        return None

    def visit_component_stmt(self, stmt: ast.ComponentStmt):
        component = OrionComponent(stmt.name.lexeme)

        # Get the style dictionaries from the instance's fields
        styles = component.fields["styles"]
        state_styles = component.fields["state_styles"]

        for body_stmt in stmt.body:
            result = body_stmt.accept(self)
            if not result: continue

            node_type, data = result
            if node_type == "style":
                prop_name, prop_value = data
                styles[prop_name] = prop_value
            elif node_type == "state":
                state_name, styles_dict = data
                state_styles[state_name] = styles_dict

        self.environment.define(stmt.name.lexeme, component)
        return None

    def visit_state_block_stmt(self, stmt: ast.StateBlock):
        state_name = stmt.name.lexeme
        styles = {}
        for prop_stmt in stmt.body:
            # Assuming state blocks only contain style props
            result = prop_stmt.accept(self)
            if result:
                node_type, data = result
                if node_type == "style":
                    prop_name, prop_value = data
                    styles[prop_name] = prop_value

        return ("state", (state_name, styles))

    def visit_style_prop_stmt(self, stmt: ast.StyleProp):
        prop_name = stmt.name.lexeme
        # A real implementation would parse values more carefully.
        prop_value = " ".join(t.lexeme for t in stmt.values)
        return ("style", (prop_name, prop_value))

    def _execute_block(self, statements: List[ast.Stmt], environment: Environment):
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self._execute(statement)
        finally:
            self.environment = previous

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

    def visit_assign_expr(self, expr: ast.Assign):
        value = self._evaluate(expr.value)
        self.environment.assign(expr.name, value)
        return value

    def visit_logical_expr(self, expr: ast.Logical):
        left = self._evaluate(expr.left)

        if expr.operator.token_type == TokenType.OR:
            if self._is_truthy(left):
                return left
        else: # AND
            if not self._is_truthy(left):
                return left

        return self._evaluate(expr.right)

    def visit_call_expr(self, expr: ast.Call):
        callee = self._evaluate(expr.callee)

        arguments = []
        for argument in expr.arguments:
            arguments.append(self._evaluate(argument))

        if not isinstance(callee, OrionCallable):
            raise OrionRuntimeError(expr.paren, "Can only call functions and classes.")

        if len(arguments) != callee.arity():
            raise OrionRuntimeError(expr.paren, f"Expected {callee.arity()} arguments but got {len(arguments)}.")

        return callee.call(self, arguments)

    def visit_get_expr(self, expr: ast.Get):
        obj = self._evaluate(expr.object)
        if isinstance(obj, OrionInstance):
            return obj.get(expr.name)

        raise OrionRuntimeError(expr.name, "Only instances have properties.")

    def visit_set_expr(self, expr: ast.Set):
        obj = self._evaluate(expr.object)

        if not isinstance(obj, OrionInstance):
            raise OrionRuntimeError(expr.name, "Only instances have fields.")

        value = self._evaluate(expr.value)
        obj.set(expr.name, value)
        return value
