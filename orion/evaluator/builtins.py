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

def _create_window(*args):
    # Mock function, does nothing
    return obj.NULL

def _sensor_read(*args):
    # Mock function, returns a dummy value
    return obj.Integer(76)

def _fan_set_speed(*args):
    # Mock function, does nothing
    return obj.NULL

# --- Create complex built-in objects like 'sensor' and 'fan' ---
sensor_read_obj = obj.Builtin(_sensor_read)
sensor_key = obj.String("read").hash_key()
sensor_obj = obj.Hash(pairs={sensor_key: obj.HashPair(key=obj.String("read"), value=sensor_read_obj)})

fan_set_speed_obj = obj.Builtin(_fan_set_speed)
fan_key = obj.String("setSpeed").hash_key()
fan_obj = obj.Hash(pairs={fan_key: obj.HashPair(key=obj.String("setSpeed"), value=fan_set_speed_obj)})


builtins = {
    "len": obj.Builtin(len_builtin),
    "createWindow": obj.Builtin(_create_window),
    "sensor": sensor_obj,
    "fan": fan_obj,
}
