from orion.object import object as obj

def len_builtin(*args):
    if len(args) != 1:
        return obj.NULL # Error: wrong number of arguments

    arg = args[0]
    if isinstance(arg, obj.String):
        return obj.Integer(len(arg.value))
    if isinstance(arg, obj.Array):
        return obj.Integer(len(arg.elements))

    return obj.NULL # Error: unsupported type

builtins = {
    "len": obj.Builtin(len_builtin),
}
