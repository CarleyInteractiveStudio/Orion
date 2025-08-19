from orion.ast import ast
from orion.object import object as obj
from orion.object.object import Module, Component
from .environment import new_enclosed_environment, Environment, new_environment
from orion.lexer.lexer import Lexer
from orion.parser.parser import Parser

# --- Module Cache (Mock File System) ---
MODULE_CACHE = {}

# --- Singleton References ---
TRUE, FALSE, NULL = obj.TRUE, obj.FALSE, obj.NULL

def eval_node(node: ast.Node, env: Environment):
    # --- Statements ---
    if isinstance(node, ast.Program): return eval_program(node, env)
    if isinstance(node, ast.BlockStatement): return eval_block_statement(node, env)
    if isinstance(node, ast.ExpressionStatement): return eval_node(node.expression, env)
    if isinstance(node, ast.ReturnStatement):
        val = eval_node(node.return_value, env)
        return obj.ReturnValue(val)
    if isinstance(node, ast.VarStatement):
        val = eval_node(node.value, env)
        env.set(node.name.value, val)
        return val
    if isinstance(node, ast.UseStatement):
        return eval_use_statement(node, env)

    # --- Expressions ---
    if isinstance(node, ast.IntegerLiteral): return obj.Integer(node.value)
    if isinstance(node, ast.StringLiteral): return obj.String(node.value)
    if isinstance(node, ast.Boolean): return TRUE if node.value else FALSE
    if isinstance(node, ast.ArrayLiteral): return obj.Array([eval_node(e, env) for e in node.elements])
    if isinstance(node, ast.HashLiteral): return eval_hash_literal(node, env)
    if isinstance(node, ast.PrefixExpression):
        right = eval_node(node.right, env)
        return eval_prefix_expression(node.operator, right)
    if isinstance(node, ast.InfixExpression):
        left = eval_node(node.left, env)
        right = eval_node(node.right, env)
        return eval_infix_expression(node.operator, left, right)
    if isinstance(node, ast.IfStatement): # Treated as an expression
        return eval_if_expression(node, env)
    if isinstance(node, ast.ComponentStatement):
        return eval_component_statement(node, env)
    if isinstance(node, ast.StyleProperty):
        return eval_style_property(node, env)
    if isinstance(node, ast.Identifier): return eval_identifier(node, env)
    if isinstance(node, ast.FunctionLiteral):
        return obj.Function(node.parameters, node.body, env)
    if isinstance(node, ast.CallExpression):
        function = eval_node(node.function, env)
        args = [eval_node(arg, env) for arg in node.arguments]
        return apply_function(function, args)
    if isinstance(node, ast.IndexExpression):
        left = eval_node(node.left, env)
        index = eval_node(node.index, env)
        return eval_index_expression(left, index)
    if isinstance(node, ast.MemberAccessExpression):
        left = eval_node(node.object, env)
        return eval_member_access_expression(left, node.property)

    return None

# --- Evaluator Helpers ---
def eval_program(program: ast.Program, env: Environment):
    result = None
    for statement in program.statements:
        result = eval_node(statement, env)
        if isinstance(result, obj.ReturnValue):
            return result.value
    return result

def eval_block_statement(block: ast.BlockStatement, env: Environment):
    result = None
    for statement in block.statements:
        result = eval_node(statement, env)
        if result and isinstance(result, obj.ReturnValue):
            return result
    return result

def eval_prefix_expression(operator: str, right: obj.Object):
    if operator == "!": return native_bool_to_boolean_object(not is_truthy(right))
    if operator == "-":
        if not right or right.object_type() != obj.ObjectType.INTEGER: return NULL
        return obj.Integer(-right.value)
    return NULL

def eval_infix_expression(operator: str, left: obj.Object, right: obj.Object):
    if left.object_type() == obj.ObjectType.INTEGER and right.object_type() == obj.ObjectType.INTEGER:
        return eval_integer_infix_expression(operator, left, right)
    if left.object_type() == obj.ObjectType.STRING and right.object_type() == obj.ObjectType.STRING:
        if operator == "+": return obj.String(left.value + right.value)
    if operator == "==": return native_bool_to_boolean_object(left == right)
    if operator == "!=": return native_bool_to_boolean_object(left != right)
    return NULL

def eval_integer_infix_expression(op: str, left: obj.Integer, right: obj.Integer):
    l, r = left.value, right.value
    if op == "+": return obj.Integer(l + r)
    if op == "-": return obj.Integer(l - r)
    if op == "*": return obj.Integer(l * r)
    if op == "/": return obj.Integer(l // r)
    if op == "<": return native_bool_to_boolean_object(l < r)
    if op == ">": return native_bool_to_boolean_object(l > r)
    if op == "==": return native_bool_to_boolean_object(l == r)
    if op == "!=": return native_bool_to_boolean_object(l != r)
    return NULL

def eval_if_expression(ie: ast.IfStatement, env: Environment):
    condition = eval_node(ie.condition, env)
    if is_truthy(condition):
        return eval_node(ie.consequence, env)
    elif ie.alternative:
        return eval_node(ie.alternative, env)
    else:
        return NULL

def eval_identifier(node: ast.Identifier, env: Environment):
    from .builtins import builtins
    val = env.get(node.value)
    if val: return val
    if node.value in builtins: return builtins[node.value]
    return NULL # Error: identifier not found

def eval_hash_literal(node: ast.HashLiteral, env: Environment) -> obj.Object:
    pairs = {}
    for key_node, value_node in node.pairs:
        key = eval_node(key_node, env)
        if not isinstance(key, obj.Hashable): return NULL # Error
        value = eval_node(value_node, env)
        hashed = key.hash_key()
        pairs[hashed] = obj.HashPair(key=key, value=value)
    return obj.Hash(pairs=pairs)

def eval_index_expression(left: obj.Object, index: obj.Object):
    if left.object_type() == obj.ObjectType.ARRAY and index.object_type() == obj.ObjectType.INTEGER:
        return eval_array_index_expression(left, index)
    if left.object_type() == obj.ObjectType.HASH:
        return eval_hash_index_expression(left, index)
    return NULL

def eval_array_index_expression(array: obj.Array, index: obj.Integer):
    idx = index.value
    max_idx = len(array.elements) - 1
    if idx < 0 or idx > max_idx: return NULL
    return array.elements[idx]

def eval_hash_index_expression(hash_obj: obj.Hash, index: obj.Object):
    if not isinstance(index, obj.Hashable): return NULL
    key = index.hash_key()
    pair = hash_obj.pairs.get(key)
    if not pair: return NULL
    return pair.value

def apply_function(fn: obj.Object, args: list[obj.Object]):
    if isinstance(fn, obj.Function):
        extended_env = new_enclosed_environment(fn.env)
        for i, param in enumerate(fn.parameters):
            extended_env.set(param.value, args[i])
        evaluated = eval_node(fn.body, extended_env)
        if isinstance(evaluated, obj.ReturnValue):
            return evaluated.value
        return evaluated
    if isinstance(fn, obj.Builtin):
        return fn.fn(*args)
    return NULL # Error: not a function

# --- Utilities ---
def is_truthy(evaluated_obj: obj.Object) -> bool:
    if evaluated_obj is NULL: return False
    if evaluated_obj is FALSE: return False
    return True

def eval_use_statement(node: ast.UseStatement, env: Environment):
    module_name = node.path.value

    # Check if module is already evaluated
    if module_name in MODULE_CACHE:
        module_obj = MODULE_CACHE[module_name]
        env.set(module_name, module_obj)
        return module_obj

    # If not, get source, parse, and eval
    source_code = MODULE_CACHE.get(f"{module_name}_source")
    if not source_code:
        return NULL # Error: module source not found

    lexer = Lexer(source_code)
    parser = Parser(lexer)
    program = parser.parse_program()

    module_env = new_environment()
    eval_node(program, module_env)

    module_obj = obj.Module(name=module_name, env=module_env)
    MODULE_CACHE[module_name] = module_obj
    env.set(module_name, module_obj)

    return module_obj

def eval_member_access_expression(left: obj.Object, prop: ast.Identifier):
    if left.object_type() == obj.ObjectType.MODULE:
        return left.env.get(prop.value)

    return NULL # Or error

def eval_component_statement(node: ast.ComponentStatement, env: Environment):
    # Create a new environment for the component's properties
    prop_env = new_environment()

    # Evaluate each statement in the component's body to populate the prop_env
    for stmt in node.body:
        eval_node(stmt, prop_env)

    # The properties are stored in the prop_env's store. We can wrap this in a Hash object.
    # This is a bit of a simplification, as we're not handling nested components correctly yet.
    properties_hash = obj.Hash(pairs={})
    for key, val in prop_env.store.items():
        # This is a simplification; we'd need to handle hash keys properly
        key_obj = obj.String(key)
        properties_hash.pairs[key_obj.hash_key()] = obj.HashPair(key=key_obj, value=val)

    comp = Component(name=node.name.value, properties=properties_hash)
    env.set(node.name.value, comp)
    return comp

def eval_style_property(node: ast.StyleProperty, env: Environment):
    # A style property is like a variable declaration in the component's scope
    # We evaluate the list of values and store it. A single value is just a list of one.
    # For simplicity, we'll just store the first value if it exists.
    if len(node.values) > 0:
        val = eval_node(node.values[0], env)
        env.set(node.name.value, val)
        return val
    return NULL


def native_bool_to_boolean_object(value: bool) -> obj.Boolean:
    return TRUE if value else FALSE
