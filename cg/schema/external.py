# -*- coding: utf-8 -*-
from copy import deepcopy

from . import constants, scout

schema_external_project = deepcopy(scout.schema_project)
schema_external_family = schema_external_project["properties"]["families"]["items"]
del schema_external_family["properties"]["require_qcok"]
del schema_external_family["properties"]["priority"]
schema_external_family["required"] = ["name", "panels"]
schema_external_family["properties"]["samples"]["items"]["properties"]["capture_kit"] = {
    "enum": constants.CAPTURE_KITS
}
