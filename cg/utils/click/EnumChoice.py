""" class to use when the click option is an Enum
based on suggestion https://github.com/pallets/click/issues/605#issuecomment-277539425
"""

from enum import EnumMeta

import rich_click as click


class EnumChoice(click.Choice):
    """class to use when the click option is an Enum"""

    def __init__(self, enum, case_sensitive=False, use_value=True):
        if isinstance(enum, tuple):
            if use_value:
                choices = (_.value for _ in enum)
            else:
                choices = (_.name for _ in enum)
        elif isinstance(enum, EnumMeta):
            if use_value:
                choices = enum
            else:
                choices = enum.__members__
        else:
            raise TypeError("`enum` must be `tuple` or `Enum`")

        if not case_sensitive:
            choices = (_.lower() for _ in choices)

        self.__enum = enum
        self.__case_sensitive = case_sensitive
        self.__use_value = use_value

        super().__init__(list(sorted(set(choices))))

    def convert(self, value, param, ctx):
        if not self.__case_sensitive:
            value = value.lower()

        value = super().convert(value, param, ctx)

        if self.__use_value:
            if not self.__case_sensitive:
                return next(_ for _ in self.__enum if _.value.lower() == value.lower())
            else:
                return next(_ for _ in self.__enum if _.value == value)
        else:
            if not self.__case_sensitive:
                return next(_ for _ in self.__enum if _.name.lower() == value.lower())
            else:
                return next(_ for _ in self.__enum if _.name == value)
