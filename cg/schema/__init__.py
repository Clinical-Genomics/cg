# -*- coding: utf-8 -*-
from . import external, fastq, rerun, rml, scout

PROJECT_SCHEMAS = dict(
    external=external.schema_project,
    fastq=fastq.schema_project,
    rerun=rerun.schema_project,
    rml=rml.schema_project,
    scout=scout.schema_project,
)
