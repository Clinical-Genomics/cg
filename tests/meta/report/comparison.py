import datetime


def is_similar_dicts(dict1, dict2):
    _is_similar = True

    for key in dict1.keys():
        _is_similar = _is_similar and is_similar_values(dict1.get(key), dict2.get(key))

    return _is_similar


def is_similar_lists(list1, list2):
    _is_similar = True

    if not list1:
        return list1 == list2

    if isinstance(list2, list):
        for value1, value2 in zip(list1, list2):
            _is_similar = _is_similar and is_similar_values(value1, value2)
    else:
        for value1 in list1:
            _is_similar = _is_similar and value1 in list2

    return _is_similar


def is_similar_values(value1, value2):

    if isinstance(value1, dict):
        return is_similar_dicts(value1, value2)

    if isinstance(value1, list):
        return is_similar_lists(value1, value2)

    if str(value1) == str(value2):
        return True

    if isinstance(value1, datetime.datetime):
        return str(value1.date()) == value2

    if is_float(value1):
        return is_float(value2) and round(float(value1), 1) == round(float(value2), 1)

    return False


def is_float(value):
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def dict_values_exists_in(a_dict: dict, a_target: str):

    all_exists = True

    for value in a_dict.values():
        all_exists = all_exists and value_exists_in(value, a_target)
    return all_exists


def value_exists_in(value, a_target: str):

    if isinstance(value, str):
        return value in a_target
    if isinstance(value, float):
        return str(round(value, 2)) in a_target or str(round(value, 1)) in a_target
    if isinstance(value, dict):
        return dict_values_exists_in(value, a_target)
    if isinstance(value, list):
        return list_values_exists_in(value, a_target)
    if isinstance(value, datetime.datetime):
        return str(value.date()) in a_target

    if str(value) in a_target:
        return True

    if isinstance(value, bool):
        return True

    return False


def list_values_exists_in(a_list: list, a_target: str):

    all_exists = True

    for value in a_list:
        all_exists = all_exists and value_exists_in(value, a_target)
    return all_exists
