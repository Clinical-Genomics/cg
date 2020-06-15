import logging

from subprocess import CalledProcessError
import subprocess

from alchy import Manager
from genotype.store import api, models
from genotype.load.vcf import load_vcf
from cg.exc import CaseNotFoundError

LOG = logging.getLogger(__name__)


class GenotypeAPI(Manager):

    """Interface with Genotype app.

    The config should contain a 'genotype' key:

        { 'database': 'mysql://localhost:3306/database' }
    """

    def __init__(self, config: dict):
        alchy_config = dict(SQLALCHEMY_DATABASE_URI=config["genotype"]["database"])
        super(GenotypeAPI, self).__init__(config=alchy_config, Model=models.Model)

        self.genotype_config = config["genotype"]["config_path"]
        self.genotype_binary = config["genotype"]["binary_path"]
        self.base_call = [self.genotype_binary, "--config", self.genotype_config]

    def upload(self, bcf_path: str, samples_sex: dict, force: bool = False):
        """Upload genotypes for a family of samples."""
        snps = api.snps()
        analyses = load_vcf(bcf_path, snps)
        for analysis_obj in analyses:
            LOG.debug("loading VCF genotypes for sample: %s", analysis_obj.sample_id)
            is_saved = api.add_analysis(self, analysis_obj, replace=force)
            if is_saved:
                LOG.info("loaded VCF genotypes for sample: %s", analysis_obj.sample_id)
            else:
                LOG.warning("skipped, found previous analysis: %s", analysis_obj.sample_id)

            if is_saved or force:
                analysis_obj.sex = samples_sex[analysis_obj.sample_id]["analysis"]
                analysis_obj.sample.sex = samples_sex[analysis_obj.sample_id]["pedigree"]
                self.commit()

    def export_sample(self, days: int = 0) -> str:
        """Export sample info."""
        trending_call = self.base_call[:]
        trending_call.extend(["export-sample", "-d", str(days)])
        try:
            LOG.info("Running Genotype API to get data.")
            LOG.debug(trending_call)
            output = subprocess.check_output(trending_call)
        except CalledProcessError as error:
            LOG.critical("Could not run command: %s", " ".join(trending_call))
            raise error
        output = output.decode("utf-8")
        # If sample not in genotype db, stdout of genotype command will be empty.
        if not output:
            raise CaseNotFoundError("samples not found in genotype db")
        return output

    def export_sample_analysis(self, days: int = 0) -> str:
        """Export analysis."""
        trending_call = self.base_call[:]
        trending_call.extend(["export-sample-analysis", "-d", str(days)])
        try:
            LOG.info("Running Genotype API to get data.")
            LOG.debug(trending_call)
            output = subprocess.check_output(trending_call)
        except CalledProcessError as error:
            LOG.critical("Could not run command: %s", " ".join(trending_call))
            raise error
        output = output.decode("utf-8")
        # If sample not in genotype db, stdout of genotype command will be empty.
        if not output:
            raise CaseNotFoundError("samples not found in genotype db")
        return output
