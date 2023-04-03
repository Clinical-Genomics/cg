from typing import Any, List, Tuple, Callable, Dict


class Dispatcher:
    def __init__(self, functions: List[Callable], input_dict: Dict[str, Any]):
        self.functions: List[Callable] = functions
        self.input_dict: Dict[str, any] = input_dict
        self.dispatch_table: Dict[Tuple[str], Callable] = self._generate_dispatch_table()

    def __call__(self, input_dict: Dict[str, Any]):
        key, values = self._parse_input_dict(input_dict)
        if key not in self.dispatch_table:
            raise ValueError(f"No matching function found for arguments: {input_dict.keys()}")
        return self.dispatch_table[key](*values)

    def _parse_input_dict(self, input_dict: Dict[str, Any]) -> [Tuple[str], Tuple[Any]]:
        parameters_not_none: List[str] = []
        values_not_none: List[Any] = []
        for parameter in input_dict.keys():
            value = input_dict[parameter]
            if value is not None:
                parameters_not_none.append(parameter)
                values_not_none.append(value)
        return tuple(parameters_not_none), tuple(values_not_none)

    def _generate_dispatch_table(self) -> Dict[Tuple[str], Callable]:
        dispatch_table = {}
        for func in self.functions:
            func_arg_names = func.__code__.co_varnames[: func.__code__.co_argcount]
            if len(set(func_arg_names)) != len(func_arg_names):
                raise ValueError(f"Duplicate argument names in function: {func.__name__}")
            dispatch_table[tuple(func_arg_names)] = func
        return dispatch_table
