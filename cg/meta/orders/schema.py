# -*- coding: utf-8 -*-
from marshmallow import Schema, fields


class BaseSample(Schema):
    name = fields.Str(required=True)
    internal_id = fields.Str()
    application = fields.Str(required=True)
    comment = fields.Str()


class PrepMixin:
    container = fields.Str(default='Tube', required=True)
    container_name = fields.Str()
    well_position = fields.Str()
    tumour = fields.Bool()
    quantity = fields.Str()
    volume = fields.Str()
    concentration = fields.Str()
    source = fields.Str(required=True)
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
    index = fields.Str()
    index_number = fields.Int()


class RmlProject(BaseProject):
    samples = fields.List(fields.Nested(RmlSample), required=True)
