from pathlib import Path

from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import Workflow
from cg.constants.gene_panel import GenePanelGenomeBuild
from cg.services.analysis_starter.configurator.file_creators.utils import (
    get_case_id_from_path,
    get_genome_build,
)
from cg.store.store import Store


class ManagedVariantsFileContentCreator:

    def __init__(self, scout_api: ScoutAPI, store: Store):
        self.scout_api = scout_api
        self.store = store

    def create(self, case_path: Path) -> list[str]:
        case_id: str = get_case_id_from_path(case_path)
        workflow = Workflow(self.store.get_case_by_internal_id(case_id).data_analysis)
        genome_build: GenePanelGenomeBuild = get_genome_build(workflow)
        return self.scout_api.export_managed_variants(genome_build)
