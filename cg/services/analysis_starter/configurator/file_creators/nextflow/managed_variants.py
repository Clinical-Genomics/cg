from pathlib import Path

from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import FileExtensions, Workflow
from cg.constants.gene_panel import GenePanelGenomeBuild
from cg.io.txt import write_txt
from cg.services.analysis_starter.configurator.file_creators.nextflow.utils import get_genome_build
from cg.store.store import Store


class ManagedVariantsFileCreator:

    def __init__(self, scout_api: ScoutAPI, store: Store):
        self.scout_api = scout_api
        self.store = store

    def create(self, case_id: str, case_path: Path) -> None:
        file_path = Path(case_path, "managed_variants").with_suffix(FileExtensions.VCF)
        content: list[str] = self._get_content(case_id)
        write_txt(file_path=file_path, content=content)

    def _get_content(self, case_id: str) -> list[str]:
        workflow = Workflow(self.store.get_case_by_internal_id(case_id).data_analysis)
        genome_build: GenePanelGenomeBuild = get_genome_build(workflow)
        return self.scout_api.export_managed_variants(genome_build)
