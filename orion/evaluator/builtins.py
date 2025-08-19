from orion.object import object as obj

def len_builtin(*args):
    if len(args) != 1:
        # Returning NULL for now, should be an error object
        return obj.NULL

    arg = args[0]
    if isinstance(arg, obj.String):
        return obj.Integer(len(arg.value))

    # Return error for unsupported type
    return obj.NULL

builtins = {
    "len": obj.Builtin(len_builtin),
}
