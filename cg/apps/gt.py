"""Interactions with the genotype tool"""

import logging

from cg.exc import CaseNotFoundError
from cg.utils.commands import Process

LOG = logging.getLogger(__name__)


class GenotypeAPI:
    """Interface with Genotype app.

    The config should contain a 'genotype' key:

        { 'database': 'mysql://localhost:3306/database' }
    """

    def __init__(self, config: dict):
        self.process = Process(
            binary=config["genotype"]["binary_path"], config=config["genotype"]["config_path"]
        )
        self.dry_run = False

    def set_dry_run(self, dry_run: bool) -> None:
        """Set the dry run state"""
        self.dry_run = dry_run

    def upload(self, bcf_path: str, samples_sex: dict, force: bool = False) -> None:
        """Upload genotypes for a family of samples."""
        upload_parameters = ["load", str(bcf_path)]
        if force:
            upload_parameters.append("--force")

        LOG.info(f"loading VCF genotypes for sample(s): {', '.join(samples_sex.keys())}")
        self.process.run_command(parameters=upload_parameters, dry_run=self.dry_run)

        for sample_id in samples_sex:
            # This is the sample sex specified by the customer
            sample_sex = samples_sex[sample_id]["pedigree"]
            self.update_sample_sex(sample_id, sample_sex)
            # This is the predicted sex based on variant calls from the workflow
            analysis_predicted_sex = samples_sex[sample_id]["analysis"]
            self.update_analysis_sex(sample_id, sex=analysis_predicted_sex)

    def update_sample_sex(self, sample_id: str, sex: str) -> None:
        """Update the sex for a sample in the genotype tool"""
        sample_sex_parameters = ["add-sex", sample_id, "-s", sex]
        LOG.debug(f"Set sex for sample {sample_id} to {sex}")
        self.process.run_command(parameters=sample_sex_parameters, dry_run=self.dry_run)

    def update_analysis_sex(self, sample_id: str, sex: str) -> None:
        """Update the predicted sex for a sample based on genotype analysis in the genotype tool"""
        analysis_sex_parameters = ["add-sex", sample_id, "-a", "sequence", sex]
        LOG.debug(f"Set predicted sex for sample {sample_id} to {sex} for the sequence analysis")
        self.process.run_command(parameters=analysis_sex_parameters, dry_run=self.dry_run)

    def export_sample(self, days: int = 0) -> str:
        """Export sample info."""
        export_sample_parameters = ["export-sample", "-d", str(days)]

        self.process.run_command(parameters=export_sample_parameters, dry_run=self.dry_run)
        output = self.process.stdout
        # If sample not in genotype db, stdout of genotype command will be empty.
        if not output:
            raise CaseNotFoundError("samples not found in genotype db")
        return output

    def export_sample_analysis(self, days: int = 0) -> str:
        """Export analysis."""
        export_sample_analysis_parameters = ["export-sample-analysis", "-d", str(days)]

        self.process.run_command(parameters=export_sample_analysis_parameters, dry_run=self.dry_run)
        output = self.process.stdout
        # If sample not in genotype db, stdout of genotype command will be empty.
        if not output:
            raise CaseNotFoundError("samples not found in genotype db")
        return output

    def __str__(self):
        return f"GenotypeAPI(dry_run: {self.dry_run})"
