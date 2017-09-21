# -*- coding: utf-8 -*-
from marshmallow import Schema, fields


class BaseSample(Schema):
    name = fields.Str(required=True)
    internal_id = fields.Str(allow_none=True)
    application = fields.Str(required=True)
    comment = fields.Str()


class PrepMixin:
    container = fields.Str(default='Tube', required=True)
    container_name = fields.Str()
    well_position = fields.Str()
    tumour = fields.Bool()
    quantity = fields.Str(allow_none=True)
    volume = fields.Str(allow_none=True)
    concentration = fields.Str(allow_none=True)
    source = fields.Str()
    priority = fields.Str(default='standard', required=True)
    require_qcok = fields.Bool(default=False)


class AnalysisMixin:
    sex = fields.Str(required=True)
    status = fields.Str(required=True)
    family_name = fields.Str(required=True)
    panels = fields.List(fields.Str(), required=True)
    father = fields.Str()
    mother = fields.Str()


class BaseProject(Schema):
    name = fields.Str(required=True)
    customer = fields.Str(required=True)
    comment = fields.Str()


class ScoutSample(BaseSample, PrepMixin, AnalysisMixin):
    pass


class ScoutProject(BaseProject):
    samples = fields.List(fields.Nested(ScoutSample), required=True)


class ExternalSample(BaseSample, AnalysisMixin):
    capture_kit = fields.Str()


class ExternalProject(BaseProject):
    samples = fields.List(fields.Nested(ExternalSample), required=True)


class FastqSample(BaseSample, PrepMixin):
    pass


class FastqProject(BaseProject):
    samples = fields.List(fields.Nested(FastqSample), required=True)


class RmlSample(BaseSample):
    pool = fields.Str(required=True)
    well_position_rml = fields.Str()
    rml_plate_name = fields.Str()
    index = fields.Str()
    index_number = fields.Int()
    index_sequence = fields.Str()


class RmlProject(BaseProject):
    samples = fields.List(fields.Nested(RmlSample), required=True)
