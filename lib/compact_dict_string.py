def compact_object_string(o, max_line_length=120, indent=0, max_depth=2 ** 32):
    if max_depth == 0:
        return ' ' * indent + '...'
    if isinstance(o, list):
        return compact_list_string(o, max_line_length, indent=indent, max_depth=max_depth)
    elif isinstance(o, tuple):
        return compact_tuple_string(o, max_line_length, indent=indent, max_depth=max_depth)
    elif isinstance(o, dict):
        return compact_dict_string(o, max_line_length, indent=indent, max_depth=max_depth)
    elif isinstance(o, str):
        return "'" + o + "'"
    else:
        return ' ' * indent + str(o)


def compact_list_string(xs: list, max_line_length=120, indent=0, closing=']', opening='[', max_depth=2 ** 32):
    # try to fit everything in one line with the default str method
    single_line_result = ' ' * indent + str(xs)
    if len(single_line_result) <= max_line_length:
        return single_line_result

    # not extra lines for [ and ]
    multi_line_result_right = ' ' * indent + opening
    for x in xs:
        prefix = ''
        multi_line_result_right += prefix + f'{compact_object_string(x, max_line_length=max_line_length, indent=indent + 1 + len(prefix), max_depth=max_depth - 1)}'.strip()
        multi_line_result_right += ',\n' + ' ' * indent
    multi_line_result_right = multi_line_result_right[:-len(',\n' + ' ' * indent)] + closing

    # extra lines for [ and ]
    multi_line_result_below = ' ' * indent + opening
    for x in xs:
        prefix = ''
        multi_line_result_below += '\n' + ' ' * (indent + 2)
        multi_line_result_below += prefix + f'{compact_object_string(x, max_line_length=max_line_length, indent=indent + 2 + len(prefix), max_depth=max_depth - 1)}'.strip()
    multi_line_result_below += ',\n' + ' ' * indent
    multi_line_result_below = multi_line_result_below + closing

    if len(multi_line_result_right.splitlines()) < len(multi_line_result_below.splitlines()):
        return multi_line_result_right
    else:
        return multi_line_result_below


def compact_tuple_string(xs: tuple, max_line_length=120, indent=0, max_depth=2 ** 32):
    return compact_list_string(list(xs), max_line_length, indent, closing=')', opening='(')


def compact_dict_string(d: dict, max_line_length=120, indent=0, max_depth=2 ** 32):
    # try to fit everything in one line with the default str method
    single_line_result = ' ' * indent + str(d)
    if len(single_line_result) <= max_line_length:
        return single_line_result

    # try to put compact value string next to the key strings
    multi_line_result_right = ' ' * indent + '{'
    for k, v in d.items():
        if isinstance(k, str):
            prefix = "'" + str(k) + "'" + ': '
        else:
            prefix = str(k) + ': '
        multi_line_result_right += prefix + f'{compact_object_string(v, max_line_length=max_line_length, indent=indent + 1 + len(prefix), max_depth=max_depth - 1)}'.strip()
        multi_line_result_right += ',\n' + ' ' * (indent)
    multi_line_result_right = multi_line_result_right[:-len(',\n' + ' ' * (indent + 1))] + '}'

    # try to put compact value string below key strings
    multi_line_result_below = ' ' * indent + '{'
    multi_line_result_below += '\n' + ' ' * (indent + 2)
    for k, v in d.items():
        prefix = "'" + str(k) + "'" + ': '
        multi_line_result_below += prefix + f'{compact_object_string(v, max_line_length=max_line_length, indent=indent + 2 + len(prefix), max_depth=max_depth - 1)}'.strip()
        multi_line_result_below += ',\n' + ' ' * (indent + 2)
    multi_line_result_below = multi_line_result_below[:-2] + '}'

    if len(multi_line_result_right.splitlines()) < len(multi_line_result_below.splitlines()):
        return multi_line_result_right
    else:
        return multi_line_result_below


if __name__ == '__main__':
    print(compact_dict_string({"body": {"game_state": {"crafting_machines": [{"name": "Basic Crafting Machine 16910", "duration": 10, "type": "CraftingMachine"}], "game_name": "test", "properties": [
        {"tier": 1, "name": "Luxuriant", "type": "Property"},
        {"tier": 1, "name": "Edible", "type": "Property"},
        {"tier": 1, "name": "Appealable", "type": "Property"}], "resources": [
        {"properties": [{"tier": 1, "name": "Luxuriant", "type": "Property"}], "name": "Wolverine", "type": "Resource"},
        {"properties": [{"tier": 1, "name": "Edible", "type": "Property"}], "name": "Lm", "type": "Resource"},
        {"properties": [{"tier": 1, "name": "Appealable", "type": "Property"}], "name": "Skittishness", "type": "Resource"}], "users": [
        {"resource_inventory": {}, "session_id": "12843d4e-8cfb-4f30-acaa-d4d9de6cf33f", "username": "testUser", "type": "User"}], "resource_discoveries":
                                                           {"testUser": [{"properties": [{"tier": 1, "name": "Luxuriant", "type": "Property"}], "name": "Wolverine", "type": "Resource"},
                                                                         {"properties": [{"tier": 1, "name": "Edible", "type": "Property"}], "name": "Lm", "type": "Resource"},
                                                                         {"properties": [{"tier": 1, "name": "Appealable", "type": "Property"}], "name": "Skittishness", "type": "Resource"}]},
                                                       "type": "GameState"}}, "http_status_code": 200, "request_token": "774ba52b-31a2-481a-9f12-537495dae993"}, max_line_length=200))
