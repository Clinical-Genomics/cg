"""Nextflow related constants."""

from cg.constants import Workflow

# TODO: Add Trana
NEXTFLOW_WORKFLOWS: list = [
    Workflow.RAREDISEASE,
    Workflow.RNAFUSION,
    Workflow.TAXPROFILER,
    Workflow.TOMTE,
]
