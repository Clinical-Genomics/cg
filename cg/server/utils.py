from wtforms.fields.choices import SelectMultipleField
from wtforms.widgets.core import CheckboxInput, TableWidget


class MultiCheckboxField(SelectMultipleField):
    widget = TableWidget()
    option_widget = CheckboxInput()
