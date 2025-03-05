import logging
from pathlib import Path

from cg.constants import FileExtensions
from cg.constants.nf_analysis import NextflowFileType
from cg.io.csv import write_csv
from cg.io.json import write_json
from cg.io.yaml import write_yaml_nextflow_style
from cg.services.analysis_starter.configurator.file_creators.abstract import FileContentCreator

LOG = logging.getLogger(__name__)

# TODO: Adapt to gene panel and variant files
FILE_TYPE_TO_EXTENSION: dict[NextflowFileType, FileExtensions] = {
    NextflowFileType.PARAMS: FileExtensions.YAML,
    NextflowFileType.SAMPLE_SHEET: FileExtensions.CSV,
    NextflowFileType.CONFIG: FileExtensions.JSON,
}

FILE_TYPE_TO_WRITER: dict[NextflowFileType, callable] = {
    NextflowFileType.PARAMS: write_yaml_nextflow_style,
    NextflowFileType.SAMPLE_SHEET: write_csv,
    NextflowFileType.CONFIG: write_json,
}


def get_file_path(case_path: Path, file_type: NextflowFileType) -> Path:
    case_id: str = case_path.name
    extension: FileExtensions = FILE_TYPE_TO_EXTENSION[file_type]
    return Path(case_path, f"{case_id}_{file_type}").with_suffix(extension)


def write_content_to_file_or_stdout(
    content: any, file_path: Path, file_type: NextflowFileType
) -> None:
    LOG.debug(f"Writing sample sheet to {file_path}")
    FILE_TYPE_TO_WRITER[file_type](content=content, file_path=file_path)


def create_file(
    content_creator: FileContentCreator,
    case_path: Path,
    file_type: NextflowFileType,
) -> None:
    file_path: Path = get_file_path(case_path=case_path, file_type=file_type)
    content: any = content_creator.create(case_path)
    write_content_to_file_or_stdout(content=content, file_path=file_path, file_type=file_type)


def get_case_id_from_path(case_path: Path) -> str:
    return case_path.name
