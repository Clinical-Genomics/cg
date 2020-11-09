""" class to use when the click option is an Enum
based on suggestion https://github.com/pallets/click/issues/605#issuecomment-277539425
"""

from enum import EnumMeta

import click


class EnumChoice(click.Choice):
    """ class to use when the click option is an Enum """

    def __init__(self, enum, case_sensitive=False, use_value=True):
        if use_value and isinstance(enum, tuple):
            choices = (_.value for _ in enum)
        elif isinstance(enum, tuple):
            choices = (_.name for _ in enum)
        elif isinstance(enum, EnumMeta):
            choices = enum.__members__
        else:
            raise TypeError("`enum` must be `tuple` or `Enum`")

        if not case_sensitive:
            choices = (_.lower() for _ in choices)

        self.__enum = enum
        self.__case_sensitive = case_sensitive

        super().__init__(list(sorted(set(choices))))

    def convert(self, value, param, ctx):
        if not self.__case_sensitive:
            value = value.lower()

        value = super().convert(value, param, ctx)

        if not self.__case_sensitive:
            return next(_ for _ in self.__enum if _.name.lower() == value.lower())
        else:
            return next(_ for _ in self.__enum if _.name == value)

    def get_metavar(self, param):
        word = self.__enum.__name__

        # from jpvanhal/inflection
        import re

        word = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", word)
        word = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", word)
        word = word.replace("-", "_").lower().split("_")

        if word[-1] == "enum":
            word.pop()

        return ("_".join(word)).upper()
