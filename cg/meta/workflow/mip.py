import datetime as dt
import gzip
import logging
import re
from pathlib import Path
from typing import Any, List, Optional

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.mip import parse_trending
from cg.apps.mip.base import MipAPI
from cg.apps.mip.confighandler import ConfigHandler
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import (
    CASE_ACTIONS,
    COLLABORATORS,
    COMBOS,
    DEFAULT_CAPTURE_KIT,
    MASTER_LIST,
    Pipeline,
)
from cg.exc import CgDataError, CgError, LimsDataError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.store import Store, models
from ruamel.yaml import safe_load

LOG = logging.getLogger(__name__)


class MipAnalysisAPI(AnalysisAPI):
    """The workflow is accessed through Trailblazer but cg provides additional conventions and
    hooks into the status database that makes managing analyses simpler"""

    def __init__(
        self,
        scout_api: ScoutAPI,
        tb_api: TrailblazerAPI,
        lims_api: LimsAPI,
        script: str,
        pipeline: str,
        conda_env: str,
        root: str,
        housekeeper_api: HousekeeperAPI,
        trailblazer_api: TrailblazerAPI,
        hermes_api: HermesApi,
        prepare_fastq_api: PrepareFastqAPI,
        status_db: Store,
        process: Process,
    ):
        super().__init__(
            housekeeper_api,
            trailblazer_api,
            hermes_api,
            lims_api,
            prepare_fastq_api,
            status_db,
            process,
            pipeline,
            scout_api,
        )
        self.db = db
        self.tb = tb_api
        self.hk = hk_api
        self.scout = scout_api
        self.lims = lims_api
        self.script = script
        self.pipeline = pipeline
        self.conda_env = conda_env
        self.root = root

    def get_pedigree_config_path(self, case_id: str) -> Path:
        return Path(self.root, case_id, "pedigree.yaml")

    def get_case_config_path(self, case_id: str) -> Path:
        return Path(self.root, case_id, "analysis", f"{case_id}_config.yaml")

    def resolve_panel_bed(self, panel_bed: Optional[str]) -> Optional[str]:
        if panel_bed:
            if panel_bed.endswith(".bed"):
                return panel_bed
            bed_version = self.db.bed_version(panel_bed)
            if not bed_version:
                raise CgError("Please provide a valid panel shortname or a path to panel.bed file!")
            return bed_version.filename

    def pedigree_config(
        self, case_obj: models.Family, pipeline: Pipeline, panel_bed: str = None
    ) -> dict:
        """Make the MIP pedigree config. Meta data for the family is taken from the family object
        and converted to MIP format via trailblazer.

        Args:
            case_obj (models.Family):
            pipeline (str): the name of the pipeline to validate the config against
            panel_bed(str): Overrides default capture kit or bypassed getting panel BED from LIMS

        Returns:
            dict: config_data (MIP format)
        """
        data = self.build_config(case_obj, pipeline=pipeline, panel_bed=panel_bed)

        # Validate and reformat to MIP pedigree config format
        config_data = ConfigHandler.make_pedigree_config(data=data, pipeline=pipeline)
        return config_data

    def build_config(
        self, case_obj: models.Family, pipeline: Pipeline, panel_bed: str = None
    ) -> dict:
        """Fetch data for creating a MIP pedigree config file"""

        def get_sample_data(link_obj):
            return {
                "sample_id": link_obj.sample.internal_id,
                "sample_display_name": link_obj.sample.name,
                "analysis_type": link_obj.sample.application_version.application.analysis_type,
                "sex": link_obj.sample.sex,
                "phenotype": link_obj.status,
                "expected_coverage": link_obj.sample.application_version.application.min_sequencing_depth,
            }

        def config_dna_sample(self, link_obj):
            sample_data = get_sample_data(link_obj)
            if sample_data["analysis_type"] == "wgs":
                sample_data["capture_kit"] = panel_bed or DEFAULT_CAPTURE_KIT
            else:
                sample_data["capture_kit"] = panel_bed or self.get_target_bed_from_lims(
                    link_obj.sample.internal_id
                )
            if link_obj.mother:
                sample_data["mother"] = link_obj.mother.internal_id
            if link_obj.father:
                sample_data["father"] = link_obj.father.internal_id
            return sample_data

        def config_rna_sample(self, link_obj):
            sample_data = get_sample_data(link_obj)
            if link_obj.mother:
                sample_data["mother"] = link_obj.mother.internal_id
            if link_obj.father:
                sample_data["father"] = link_obj.father.internal_id
            return sample_data

        dispatch = {
            Pipeline.MIP_DNA: config_dna_sample,
            Pipeline.MIP_RNA: config_rna_sample,
        }

        data = {
            "case": case_obj.internal_id,
            "default_gene_panels": case_obj.panels,
        }
        config_sample = dispatch[pipeline]
        data["samples"] = [config_sample(self, link_obj=link_obj) for link_obj in case_obj.links]
        return data

    @staticmethod
    def name_file(
        lane: int,
        flowcell: str,
        sample: str,
        read: int,
        undetermined: bool = False,
        date: dt.datetime = None,
        index: str = None,
    ) -> str:
        """Name a FASTQ file following MIP conventions."""
        flowcell = f"{flowcell}-undetermined" if undetermined else flowcell
        date_str = date.strftime("%y%m%d") if date else "171015"
        index = index or "XXXXXX"
        return f"{lane}_{date_str}_{flowcell}_{sample}_{index}_{read}.fastq.gz"

    def link_file(self, family: str, sample: str, analysis_type: str, files: List[dict]):
        """Link FASTQ files for a sample."""
        fastq_dir = Path(self.root) / family / analysis_type / sample / "fastq"
        fastq_dir.mkdir(parents=True, exist_ok=True)
        for fastq_data in files:
            fastq_path = Path(fastq_data["path"])
            fastq_name = self.name_file(
                lane=fastq_data["lane"],
                flowcell=fastq_data["flowcell"],
                sample=sample,
                read=fastq_data["read"],
                undetermined=fastq_data["undetermined"],
            )
            dest_path = fastq_dir / fastq_name
            if not dest_path.exists():
                LOG.info(f"linking: {fastq_path} -> {dest_path}")
                dest_path.symlink_to(fastq_path)
            else:
                LOG.debug(f"destination path already exists: {dest_path}")

    def link_sample(self, sample: models.Sample, case_id: str):
        """Link FASTQ files for a sample."""
        file_objs = self.hk.files(bundle=sample.internal_id, tags=["fastq"])
        files = []

        for file_obj in file_objs:
            # figure out flowcell name from header
            with gzip.open(file_obj.full_path) as handle:
                header_line = handle.readline().decode()
                header_info = self.fastq_header(header_line)

            data = {
                "path": file_obj.full_path,
                "lane": int(header_info["lane"]),
                "flowcell": header_info["flowcell"],
                "read": int(header_info["readnumber"]),
                "undetermined": ("_Undetermined_" in file_obj.path),
            }
            # look for tile identifier (HiSeq X runs)
            matches = re.findall(r"-l[1-9]t([1-9]{2})_", file_obj.path)
            if len(matches) > 0:
                data["flowcell"] = f"{data['flowcell']}-{matches[0]}"
            files.append(data)

        self.link_file(
            family=case_id,
            sample=sample.internal_id,
            analysis_type=sample.application_version.application.analysis_type,
            files=files,
        )

    def panel(self, case_obj: models.Family) -> List[str]:
        """Create the aggregated panel file."""
        all_panels = self.convert_panels(case_obj.customer.internal_id, case_obj.panels)
        return self.scout.export_panels(all_panels)

    def write_panel(self, case_id: str, content: List[str]):
        """Write the gene panel to case dir"""
        out_dir = Path(self.root, case_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = Path(out_dir, "gene_panels.bed")
        with out_path.open("w") as out_handle:
            out_handle.write("\n".join(content))

    @staticmethod
    def convert_panels(customer: str, default_panels: List[str]) -> List[str]:
        """Convert between default panels and all panels included in gene list."""
        # check if all default panels are part of master list
        if customer in COLLABORATORS and all(panel in MASTER_LIST for panel in default_panels):
            return MASTER_LIST

        # the rest are handled the same way
        all_panels = set(default_panels)

        # fill in extra panels if selection is part of a combo
        for panel in default_panels:
            if panel in COMBOS:
                for extra_panel in COMBOS[panel]:
                    all_panels.add(extra_panel)

        # add OMIM to every panel choice
        all_panels.add("OMIM-AUTO")

        return list(all_panels)

    def _get_latest_raw_file(self, family_id: str, tag: str) -> Any:
        """Get a python object file for a tag and a family ."""

        last_version = self.hk.last_version(bundle=family_id)

        analysis_files = self.hk.files(bundle=family_id, version=last_version.id, tags=[tag]).all()

        if analysis_files:
            analysis_file_raw = self._open_bundle_file(analysis_files[0].path)
        else:
            raise LOG.warning(
                "No post analysis files received from DeliverAPI for '%s'",
                family_id,
            )

        return analysis_file_raw

    def _open_bundle_file(self, relative_file_path: str) -> Any:
        """Open a bundle file and return it as an Python object."""

        full_file_path = Path(self.hk.get_root_dir()).joinpath(relative_file_path)
        return safe_load(open(full_file_path))

    def get_latest_metadata(self, family_id: str) -> dict:
        """Get the latest trending data for a family."""

        mip_config_raw = self._get_latest_raw_file(family_id=family_id, tag="mip-config")
        qcmetrics_raw = self._get_latest_raw_file(family_id=family_id, tag="qcmetrics")
        sampleinfo_raw = self._get_latest_raw_file(family_id=family_id, tag="sampleinfo")
        trending = dict()
        if mip_config_raw and qcmetrics_raw and sampleinfo_raw:
            try:
                trending = parse_trending.parse_mip_analysis(
                    mip_config_raw=mip_config_raw,
                    qcmetrics_raw=qcmetrics_raw,
                    sampleinfo_raw=sampleinfo_raw,
                )
            except KeyError as error:
                LOG.warning(
                    "get_latest_metadata failed for '%s', missing key: %s",
                    family_id,
                    error.args[0],
                )
                LOG.warning(
                    "get_latest_metadata failed for '%s', missing key: %s",
                    family_id,
                    error.args[0],
                )
                trending = {}
        return trending

    @staticmethod
    def is_dna_only_case(case_obj: models.Family) -> bool:
        """Returns True if all samples of a case has dna application type"""

        return all(
            _link.sample.application_version.application.analysis_type not in "wts"
            for _link in case_obj.links
        )

    @staticmethod
    def get_skip_evaluation_flag(case_obj: models.Family) -> bool:
        """If any sample in this case is downsampled or external, returns true"""
        for link_obj in case_obj.links:
            downsampled = isinstance(link_obj.sample.downsampled_to, int)
            external = link_obj.sample.application_version.application.is_external
            if downsampled or external:
                LOG.info(
                    "%s: downsampled/external - skip evaluation",
                    link_obj.sample.internal_id,
                )
                return True
        return False

    def get_application_type(self, case_id: str) -> str:
        pedigree_config_dict = safe_load(open(self.get_pedigree_config_path(case_id=case_id)))
        analysis_types = {
            sample.get("analysis_type")
            for sample in pedigree_config_dict["samples"]
            if sample.get("analysis_type")
        }

        if len(analysis_types) == 1:
            return analysis_types.pop()
        return "wgs"

    def get_case_path(self, case_id: str) -> Path:
        return Path(self.root, case_id)

    def get_trailblazer_config_path(self, case_id: str) -> Path:
        return Path(self.get_case_path(case_id=case_id), "analysis", "slurm_job_ids.yaml")
