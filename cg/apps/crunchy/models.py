"""Models to help parsing relevant data"""

import marshmallow as ma

from cg.utils.date import SIMPLE_DATE_FORMAT


class CrunchyFileSchema(ma.Schema):
    """Schema with information from spring metadata info"""

    path = ma.fields.Str(required=True, error_messages={"required": "Path is required."})
    file = ma.fields.Str(
        required=True,
        validate=ma.validate.OneOf(["first_read", "second_read", "spring"]),
        error_messages={"required": "File needs to be specified."},
    )
    checksum = ma.fields.Str()
    algorithm = ma.fields.Str()
    updated = ma.fields.DateTime(SIMPLE_DATE_FORMAT)
