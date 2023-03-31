from typing import Any, List, Tuple, Callable, Dict
import itertools
import inspect


class Dispatcher:
    def __init__(self, functions: List[Callable], input_dict: Dict[str, Any]):
        self.functions: List[Callable] = functions
        self.input_dict: Dict[str, any] = input_dict
        self.dispatch_table = self._generate_dispatch_table()

    def __call__(self, input_dict: Dict[str, Any]):
        key = self._get_param_names(input_dict)[0]
        values = self._get_param_names(input_dict)[1]
        if key not in self.dispatch_table:
            raise ValueError(f"No matching function found for arguments: {input_dict.keys()}")
        return self.dispatch_table[key](*values)

    def _get_param_names(self, input_dict: Dict[str, Any]):
        parameters_not_none = []
        values_not_none = []
        for parameter in input_dict.keys():
            value = input_dict[parameter]
            if value is not None:
                parameters_not_none.append(parameter)
                values_not_none.append(value)
        return [tuple(parameters_not_none), tuple(values_not_none)]

    def _generate_dispatch_table(self):
        dispatch_table = {}
        for func in self.functions:
            func_arg_names = func.__code__.co_varnames[: func.__code__.co_argcount]
            # check that all argument names are unique
            if len(set(func_arg_names)) != len(func_arg_names):
                raise ValueError(f"Duplicate argument names in function: {func.__name__}")
            # add the function to the dispatch table
            dispatch_table[tuple(func_arg_names)] = func
        return dispatch_table
