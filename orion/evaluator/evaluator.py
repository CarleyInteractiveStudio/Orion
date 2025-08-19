from orion.ast import ast
from orion.object import object as obj
from orion.evaluator.environment import Environment

# Singleton references
TRUE = obj.TRUE
FALSE = obj.FALSE
NULL = obj.NULL

def eval_node(node: ast.Node, env: Environment):
    """The main evaluation function. It dispatches to other functions based on node type."""

    # Statements
    if isinstance(node, ast.Program):
        return eval_program(node.statements, env)
    if isinstance(node, ast.BlockStatement):
        return eval_block_statement(node.statements, env)
    if isinstance(node, ast.ExpressionStatement):
        return eval_node(node.expression, env)
    if isinstance(node, ast.ReturnStatement):
        val = eval_node(node.return_value, env)
        return obj.ReturnValue(val)
    if isinstance(node, ast.VarStatement):
        val = eval_node(node.value, env)
        env.set(node.name.value, val)
        return val # Assignment can be an expression in some languages
    if isinstance(node, ast.IfStatement):
        return eval_if_statement(node, env)

    # Expressions
    if isinstance(node, ast.IntegerLiteral):
        return obj.Integer(node.value)
    if isinstance(node, ast.Boolean):
        return TRUE if node.value else FALSE
    if isinstance(node, ast.Identifier):
        return eval_identifier(node, env)
    if isinstance(node, ast.PrefixExpression):
        right = eval_node(node.right, env)
        return eval_prefix_expression(node.operator, right)
    if isinstance(node, ast.InfixExpression):
        left = eval_node(node.left, env)
        right = eval_node(node.right, env)
        return eval_infix_expression(node.operator, left, right)

    return None

def eval_program(stmts: list[ast.Statement], env: Environment):
    result = None
    for stmt in stmts:
        result = eval_node(stmt, env)
        if isinstance(result, obj.ReturnValue):
            return result.value
    return result

def eval_block_statement(stmts: list[ast.Statement], env: Environment):
    result = None
    for stmt in stmts:
        result = eval_node(stmt, env)
        if result is not None and result.object_type() == obj.ObjectType.RETURN_VALUE:
            return result
    return result

def eval_prefix_expression(operator: str, right: obj.Object):
    if operator == "!":
        return eval_bang_operator_expression(right)
    if operator == "-":
        return eval_minus_prefix_operator_expression(right)
    return NULL

def eval_bang_operator_expression(right: obj.Object):
    return FALSE if is_truthy(right) else TRUE

def eval_minus_prefix_operator_expression(right: obj.Object):
    if right.object_type() != obj.ObjectType.INTEGER:
        return NULL
    return obj.Integer(-right.value)

def eval_infix_expression(operator: str, left: obj.Object, right: obj.Object):
    if left.object_type() == obj.ObjectType.INTEGER and right.object_type() == obj.ObjectType.INTEGER:
        return eval_integer_infix_expression(operator, left, right)
    if operator == "==":
        return native_bool_to_boolean_object(left is right)
    if operator == "!=":
        return native_bool_to_boolean_object(left is not right)
    return NULL

def eval_integer_infix_expression(operator: str, left: obj.Integer, right: obj.Integer):
    left_val, right_val = left.value, right.value
    if operator == "+": return obj.Integer(left_val + right_val)
    if operator == "-": return obj.Integer(left_val - right_val)
    if operator == "*": return obj.Integer(left_val * right_val)
    if operator == "/": return obj.Integer(left_val // right_val)
    if operator == "<": return native_bool_to_boolean_object(left_val < right_val)
    if operator == ">": return native_bool_to_boolean_object(left_val > right_val)
    if operator == "==": return native_bool_to_boolean_object(left_val == right_val)
    if operator == "!=": return native_bool_to_boolean_object(left_val != right_val)
    return NULL

def eval_if_statement(node: ast.IfStatement, env: Environment):
    condition = eval_node(node.condition, env)
    if is_truthy(condition):
        return eval_node(node.consequence, env)
    elif node.alternative is not None:
        return eval_node(node.alternative, env)
    else:
        return NULL

def eval_identifier(node: ast.Identifier, env: Environment) -> obj.Object:
    val = env.get(node.value)
    if val is None:
        # For now, we'll just return NULL if a variable is not found.
        # Later, this should be a runtime error.
        return NULL
    return val

def is_truthy(evaluated_obj: obj.Object) -> bool:
    if evaluated_obj is NULL: return False
    if evaluated_obj is FALSE: return False
    return True

def native_bool_to_boolean_object(value: bool) -> obj.Boolean:
    return TRUE if value else FALSE
