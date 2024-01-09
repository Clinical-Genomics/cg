from typing import Any, Callable


class Dispatcher:
    def __init__(self, functions: list[Callable], input_dict: dict[str, Any]):
        """Initialize the dispatcher with a list of functions and an input dict"""
        self.functions: list[Callable] = functions
        self.input_dict: dict[str, any] = input_dict
        self.dispatch_table: dict[tuple[str], Callable] = self._generate_dispatch_table()

    def __call__(self):
        """Call the dispatcher with the input dict"""
        parameters_not_none, parameter_values_not_none = self._parse_input_dict(self.input_dict)
        if parameters_not_none not in self.dispatch_table:
            raise ValueError(f"No matching function found for arguments: {parameters_not_none}")
        return self.dispatch_table[parameters_not_none](
            **dict(zip(parameters_not_none, parameter_values_not_none))
        )

    def _parse_input_dict(self, input_dict: dict[str, Any]) -> [tuple[str], tuple[Any]]:
        """Parse the input dict and return a tuple of parameters and values that are not None"""
        parameters_not_none: list[str] = []
        values_not_none: list[Any] = []
        for parameter in sorted(input_dict.keys()):
            value = input_dict[parameter]
            if value is not None:
                parameters_not_none.append(parameter)
                values_not_none.append(value)
        return tuple(parameters_not_none), tuple(values_not_none)

    def _generate_dispatch_table(self) -> dict[tuple[str], Callable]:
        """Generate a dispatch table from the list of functions"""
        dispatch_table = {}
        for func in self.functions:
            func_arg_names: list[str] = sorted(
                func.__code__.co_varnames[: func.__code__.co_argcount]
            )
            func_arg_names: list[str] = [arg for arg in func_arg_names if arg != "self"]
            if len(set(func_arg_names)) != len(func_arg_names):
                raise ValueError(f"Duplicate argument names in function: {func.__name__}")
            dispatch_table[tuple(func_arg_names)] = func
        return dispatch_table
