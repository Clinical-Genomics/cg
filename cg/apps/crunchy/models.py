"""Models to help parsing relevant data"""

import marshmallow as ma


class FileInfoSchema(ma.Schema):
    """Schema with information from spring metadata file info"""


class SpringMetadataSchema(ma.Schema):
    """Schema with information from spring metadata info"""

    path = ma.fields.Str(required=True, error_messages={"required": "Path is required."})
    file = ma.fields.Str(required=True, error_messages={"required": "File needs to be specified."})
