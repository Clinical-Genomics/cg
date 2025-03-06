import logging
from pathlib import Path

from cg.constants import FileExtensions, Workflow
from cg.constants.gene_panel import GenePanelGenomeBuild
from cg.constants.nf_analysis import NextflowFileType
from cg.io.csv import write_csv
from cg.io.json import write_json
from cg.io.txt import write_txt
from cg.io.yaml import write_yaml_nextflow_style
from cg.services.analysis_starter.configurator.file_creators.abstract import FileContentCreator

LOG = logging.getLogger(__name__)

FILE_TYPE_TO_EXTENSION: dict[NextflowFileType, str] = {
    NextflowFileType.PARAMS: FileExtensions.YAML,
    NextflowFileType.SAMPLE_SHEET: FileExtensions.CSV,
    NextflowFileType.CONFIG: FileExtensions.JSON,
    NextflowFileType.GENE_PANEL: FileExtensions.BED,
    NextflowFileType.MANAGED_VARIANTS: FileExtensions.VCF,
}

# TODO: Adapt to gene panel and variant files
FILE_TYPE_TO_WRITER: dict[NextflowFileType, callable] = {
    NextflowFileType.PARAMS: write_yaml_nextflow_style,
    NextflowFileType.SAMPLE_SHEET: write_csv,
    NextflowFileType.CONFIG: write_json,
    NextflowFileType.MANAGED_VARIANTS: write_txt,
}


def get_file_name(file_type: NextflowFileType) -> str:
    if file_type in [
        NextflowFileType.CONFIG,
        NextflowFileType.PARAMS,
        NextflowFileType.SAMPLE_SHEET,
    ]:
        return "{case_id}_" + file_type
    else:
        return file_type


def get_file_path(case_path: Path, file_type: NextflowFileType) -> Path:
    case_id: str = case_path.name
    extension: str = FILE_TYPE_TO_EXTENSION[file_type]
    file_name: str = get_file_name(file_type).format(case_id=case_id)
    return Path(case_path, file_name).with_suffix(extension)


def write_content_to_file(content: any, file_path: Path, file_type: NextflowFileType) -> None:
    LOG.debug(f"Writing sample sheet to {file_path}")
    FILE_TYPE_TO_WRITER[file_type](content=content, file_path=file_path)


def create_file(
    content_creator: FileContentCreator,
    case_path: Path,
    file_type: NextflowFileType,
) -> None:
    file_path: Path = get_file_path(case_path=case_path, file_type=file_type)
    content: any = content_creator.create(case_path)
    write_content_to_file(content=content, file_path=file_path, file_type=file_type)


def get_case_id_from_path(case_path: Path) -> str:
    return case_path.name


def get_genome_build(workflow: Workflow) -> GenePanelGenomeBuild:
    """Return genome build for the given Workflow."""
    workflow_to_genome_build: dict[Workflow, GenePanelGenomeBuild] = {
        Workflow.NALLO: GenePanelGenomeBuild.hg38,
        Workflow.RAREDISEASE: GenePanelGenomeBuild.hg19,
        Workflow.TOMTE: GenePanelGenomeBuild.hg38,
    }
    return workflow_to_genome_build.get(workflow)
