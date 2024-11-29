def ujson_enable():
    import json

    import ujson

    def json_dumps(*args, **kwargs):
        _ = kwargs.pop("cls", None)

        indent = kwargs.pop("indent", 0) or 0
        return ujson.dumps(indent=indent, *args, **kwargs)

    json.dumps = json_dumps
    json.loads = ujson.loads
