from cg.constants import Workflow
from cg.constants.gene_panel import GenePanelGenomeBuild


def get_genome_build(workflow: Workflow) -> GenePanelGenomeBuild | None:
    """Return genome build for the given Workflow."""
    workflow_to_genome_build: dict[Workflow, GenePanelGenomeBuild] = {
        Workflow.MIP_DNA: GenePanelGenomeBuild.hg19,
        Workflow.NALLO: GenePanelGenomeBuild.hg38,
        Workflow.RAREDISEASE: GenePanelGenomeBuild.hg19,
        Workflow.TOMTE: GenePanelGenomeBuild.hg38,
    }
    return workflow_to_genome_build.get(workflow)
