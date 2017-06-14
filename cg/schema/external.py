# -*- coding: utf-8 -*-
from copy import deepcopy

from . import constants, scout

schema_project = deepcopy(scout.schema_project)
schema_family = schema_project["properties"]["families"]["items"]
del schema_family["properties"]["require_qcok"]
del schema_family["properties"]["priority"]
schema_family["required"] = ["name", "panels"]
schema_family["properties"]["samples"]["items"]["properties"]["capture_kit"] = {
    "enum": constants.CAPTURE_KITS
}
