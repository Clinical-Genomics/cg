from enum import Enum, EnumMeta

from flask_admin.form import Select2Field


class EnumField:
    @staticmethod
    def get_name(enum_instance):
        return enum_instance.name

    @staticmethod
    def get_value(enum_instance):
        return enum_instance.value

    default_label_function = get_value

    def apply_choices(
        self, enum_class: EnumMeta, label_function=default_label_function, kwargs=None
    ):
        if not kwargs:
            kwargs = dict()
        choices = [
            (member.value, label_function(member))
            for name, member in enum_class.__members__.items()
        ]
        kwargs["choices"] = choices
        kwargs["coerce"] = self.coerce
        return kwargs

    @staticmethod
    def coerce(data):
        if isinstance(data, Enum):
            return data.value
        return str(data)


class SelectEnumField(Select2Field, EnumField):
    def __init__(
        self, *args, enum_class: EnumMeta, label_function=EnumField.default_label_function, **kwargs
    ):
        kwargs = self.apply_choices(enum_class, label_function, kwargs)
        super().__init__(*args, **kwargs)
