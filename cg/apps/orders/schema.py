# -*- coding: utf-8 -*-
from marshmallow import Schema, fields


class BaseSample(Schema):
    name = fields.Str(required=True)
    internal = fields.Str()
    application = fields.Str(required=True)


class BaseFamily(Schema):
    name = fields.Str(required=True)
    panels = fields.List(fields.Str(), required=True)


class BaseProject(Schema):
    name = fields.Str(required=True)
    customer = fields.Str(required=True)


class AnalysisSample(Schema):
    sex = fields.Str()
    status = fields.Str()


class PrepSample(BaseSample):
    container = fields.Str(default='Tube')
    container_name = fields.Str()
    well_position = fields.Str()
    tumour = fields.Bool()
    quantity = fields.Str()
    source = fields.Str()


class ScoutSample(PrepSample, AnalysisSample):
    father = fields.Str()
    mother = fields.Str()


class ScoutFamily(BaseFamily):
    priority = fields.Str(required=True, default='standard')
    require_qcok = fields.Bool()
    samples = fields.List(fields.Nested(ScoutSample), required=True)


class ScoutProject(BaseProject):
    families = fields.List(fields.Nested(ScoutFamily), required=True)


class ExternalSample(BaseSample, AnalysisSample):
    capture_kit = fields.Str()


class ExternalFamily(BaseFamily):
    samples = fields.List(fields.Nested(ExternalSample), required=True)


class ExternalProject(BaseProject):
    families = fields.List(fields.Nested(ExternalSample), required=True)


class FastqProject(BaseProject):
    samples = fields.List(fields.Nested(PrepSample), required=True)


class RerunFamily(BaseFamily):
    samples = fields.List(fields.Nested(AnalysisSample), required=True)


class RerunProject(BaseProject):
    families = fields.List(fields.Nested(RerunFamily), required=True)
