"""Code for talking to Scout regarding uploads"""

import logging
from pathlib import Path
from subprocess import CalledProcessError

from cg.apps.scout.scout_export import ScoutExportCase, Variant
from cg.constants.constants import FileFormat
from cg.constants.gene_panel import GENOME_BUILD_37
from cg.constants.scout import ScoutCustomCaseReportTags
from cg.exc import ScoutUploadError
from cg.io.controller import ReadFile, ReadStream
from cg.models.scout.scout_load_config import ScoutLoadConfig
from cg.services.slurm_upload_service.slurm_upload_service import SlurmUploadService
from cg.utils.commands import Process

LOG = logging.getLogger(__name__)


class ScoutAPI:
    """Interface to Scout."""

    def __init__(self, config, slurm_upload_service: SlurmUploadService):
        binary_path = config["scout"]["binary_path"]
        config_path = config["scout"]["config_path"]
        self.process = Process(binary=binary_path, config=config_path)
        self.slurm_upload_service = slurm_upload_service
        self.scout_base_command = f"{binary_path} --config {config_path}"

    def upload(self, scout_load_config: Path, force: bool = False) -> None:
        """Load analysis of a new family into Scout."""

        scout_config: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=scout_load_config
        )
        scout_load_config_object = ScoutLoadConfig(**scout_config)
        case_id: str = scout_load_config_object.family
        existing_case: ScoutExportCase | None = self.get_case(case_id)
        load_command = ["load", "case", str(scout_load_config)]
        if existing_case:
            if force or scout_load_config_object.analysis_date > existing_case.analysis_date:
                load_command.append("--update")
                LOG.info("update existing Scout case")
            else:
                existing_date = existing_case.analysis_date.date()
                LOG.warning(f"Analysis of case already loaded: {existing_date}")
                return
        LOG.debug("load new Scout case")
        self.process.run_command(load_command)
        LOG.debug("Case loaded successfully to Scout")

    def export_panels(
        self, panels: list[str], build: str = GENOME_BUILD_37, dry_run: bool = False
    ) -> list[str]:
        """Pass through to export of a list of gene panels.

        Return list of lines in bed format
        """
        export_panels_command = ["export", "panel", "--bed"]
        export_panels_command.extend(iter(panels))

        if build:
            export_panels_command.extend(["--build", build])

        try:
            self.process.run_command(export_panels_command, dry_run=dry_run)
            if not self.process.stdout:
                return []
        except CalledProcessError:
            LOG.info("Could not find panels")
            return []

        return list(self.process.stdout_lines())

    def export_managed_variants(self, genome_build: str = GENOME_BUILD_37) -> list[str]:
        """Export a list of managed variants."""
        export_command = ["export", "managed"]
        if genome_build:
            export_command.extend(["--build", genome_build])
        try:
            self.process.run_command(export_command)
            if not self.process.stdout:
                return []
        except CalledProcessError:
            LOG.info("Could not export managed variants")
            return []
        return list(self.process.stdout_lines())

    def get_genes(self, panel_id: str, build: str = None) -> list[dict]:
        """Return panel genes."""
        export_panel_command = ["export", "panel", panel_id]
        if build:
            export_panel_command.extend(["--build", build])

        try:
            self.process.run_command(export_panel_command)
            if not self.process.stdout:
                return []
        except CalledProcessError:
            LOG.info(f"Could not find panel {panel_id}")
            return []

        panel_genes = []
        for gene_line in self.process.stdout_lines():
            if gene_line.startswith("#"):
                continue
            gene_info = gene_line.strip().split("\t")
            if len(gene_info) <= 1:
                continue
            panel_genes.append({"hgnc_id": int(gene_info[0]), "hgnc_symbol": gene_info[1]})

        return panel_genes

    def get_causative_variants(self, case_id: str) -> list[Variant]:
        """
        Get causative variants for a case.
        """
        get_causatives_command = ["export", "variants", "--json", "--case-id", case_id]
        try:
            self.process.run_command(get_causatives_command)
            if not self.process.stdout:
                return []
        except CalledProcessError:
            LOG.warning(f"Could not find case {case_id} in scout")
            return []
        variants: list[Variant] = [
            Variant(**variant_info)
            for variant_info in ReadStream.get_content_from_stream(
                file_format=FileFormat.JSON, stream=self.process.stdout
            )
        ]

        return variants

    def get_case(self, case_id: str) -> ScoutExportCase | None:
        """Fetch a case from Scout"""
        cases: list[ScoutExportCase] = self.get_cases(case_id=case_id)
        return cases[0] if cases else None

    def get_cases(
        self,
        case_id: str | None = None,
        reruns: bool = False,
        finished: bool = False,
        status: str | None = None,
        days_ago: int = None,
    ) -> list[ScoutExportCase]:
        """Interact with cases existing in the database."""
        get_cases_command = ["export", "cases", "--json"]
        if case_id:
            get_cases_command.extend(["--case-id", case_id])

        elif status:
            get_cases_command.extend(["--status", status])

        elif finished:
            get_cases_command.append("--finished")

        if reruns:
            LOG.info("Fetching cases that are reruns")
            get_cases_command.append("--reruns")

        if days_ago:
            get_cases_command.extend(["--within-days", str(days_ago)])

        try:
            self.process.run_command(get_cases_command)
            if not self.process.stdout:
                return []
        except CalledProcessError:
            LOG.info("Could not find cases")
            return []

        cases: list[ScoutExportCase] = []
        for case_export in ReadStream.get_content_from_stream(
            file_format=FileFormat.JSON, stream=self.process.stdout
        ):
            LOG.info(f"Validating case {case_export.get('_id')}")
            cases.append(ScoutExportCase.model_validate(case_export))
        return cases

    def get_solved_cases(self, days_ago: int) -> list[ScoutExportCase]:
        """
        Get cases solved within chosen time span.
        """
        return self.get_cases(status="solved", days_ago=days_ago)

    def upload_delivery_report(self, report_path: str, case_id: str, update: bool = False) -> None:
        """Load a delivery report into a case in the database.
        If the report already exists the function will exit.
        If the user want to load a report that is already in the database
        'update' has to be 'True'."""

        upload_command: list[str] = ["load", "delivery-report", case_id, report_path]

        if update:
            upload_command.append("--update")

        try:
            LOG.info(f"Uploading delivery report {report_path} to case {case_id}")
            self.process.run_command(upload_command)
        except CalledProcessError:
            LOG.warning("Something went wrong when uploading delivery report")

    def upload_report(self, case_id: str, report_path: str, report_type: str) -> None:
        """Load report into a case in the database."""

        upload_report_command: list[str] = [
            "load",
            "report",
            "-t",
            report_type,
            case_id,
            report_path,
        ]

        try:
            LOG.info(f"Uploading {report_type} report to case {case_id}")
            self.process.run_command(upload_report_command)
        except CalledProcessError:
            LOG.warning(f"Something went wrong when uploading {report_type} for case {case_id}")

    def upload_fusion_report(self, case_id: str, report_path: str, research: bool) -> None:
        """Load a fusion report into a case in the database."""

        report_type: str = (
            ScoutCustomCaseReportTags.GENE_FUSION_RESEARCH
            if research
            else ScoutCustomCaseReportTags.GENE_FUSION
        )
        self.upload_report(case_id=case_id, report_path=report_path, report_type=report_type)

    def upload_splice_junctions_bed(
        self, file_path: str, case_id: str, customer_sample_id: str
    ) -> None:
        """Load a splice junctions bed file into a case in the database."""

        upload_command: list[str] = [
            "update",
            "individual",
            "--case-id",
            case_id,
            "--ind",
            customer_sample_id,
            "splice_junctions_bed",
            file_path,
        ]

        try:
            LOG.info(f"Uploading splice junctions bed file {file_path} to case {case_id}.")
            self.process.run_command(upload_command)
        except CalledProcessError as error:
            raise ScoutUploadError(
                "Something went wrong when uploading the splice junctions bed file."
            ) from error

    def upload_rna_coverage_bigwig(
        self, file_path: str, case_id: str, customer_sample_id: str
    ) -> None:
        """Load a rna coverage bigwig file into a case in the database."""

        upload_command: list[str] = [
            "update",
            "individual",
            "--case-id",
            case_id,
            "--ind",
            customer_sample_id,
            "rna_coverage_bigwig",
            file_path,
        ]

        try:
            LOG.info(f"Uploading rna coverage bigwig file {file_path} to case {case_id}")
            self.process.run_command(upload_command)
        except CalledProcessError as error:
            raise ScoutUploadError(
                "Something went wrong when uploading rna coverage bigwig file"
            ) from error

    def upload_rna_alignment_file(
        self, case_id: str, customer_sample_id: str, file_path: str
    ) -> None:
        """Load an RNA alignment CRAM file into a case in the database."""

        upload_command: list[str] = [
            "update",
            "individual",
            "--case-id",
            case_id,
            "--ind",
            customer_sample_id,
            "rna_alignment_path",
            file_path,
        ]

        try:
            LOG.info(f"Uploading RNA alignment CRAM file {file_path} to case {case_id}")
            self.process.run_command(upload_command)
        except CalledProcessError as error:
            raise ScoutUploadError(
                "Something went wrong when uploading the RNA alignment CRAM file"
            ) from error
