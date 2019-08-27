# -*- coding: utf-8 -*-
import logging

from alchy import Manager
from genotype.store import api, models, trending
from genotype.load.vcf import load_vcf

LOG = logging.getLogger(__name__)


class GenotypeAPI(Manager):

    """Interface with Genotype app.

    The config should contain a 'genotype' key:

        { 'database': 'mysql://localhost:3306/database' }
    """

    def __init__(self, config: dict):
        alchy_config = dict(SQLALCHEMY_DATABASE_URI=config['genotype']['database'])
        super(GenotypeAPI, self).__init__(config=alchy_config, Model=models.Model)

        self.genotype_config = config['genotype']['config_path']
        self.genotype_binary = config['genotype']['binary_path']
        self.genotype_database = config['genotype']['database']
        self.base_call = [self.genotype_binary, '--config', self.genotype_config, 
                            '--database', self.genotype_database]

    def upload(self, bcf_path: str, samples_sex: dict, force: bool=False):
        """Upload genotypes for a family of samples."""
        snps = api.snps()
        analyses = load_vcf(bcf_path, snps)
        for analysis_obj in analyses:
            LOG.debug('loading VCF genotypes for sample: %s', analysis_obj.sample_id)
            is_saved = api.add_analysis(self, analysis_obj, replace=force)
            if is_saved:
                LOG.info('loaded VCF genotypes for sample: %s', analysis_obj.sample_id)
            else:
                LOG.warning('skipped, found previous analysis: %s', analysis_obj.sample_id)

            if is_saved or force:
                analysis_obj.sex = samples_sex[analysis_obj.sample_id]['analysis']
                analysis_obj.sample.sex = samples_sex[analysis_obj.sample_id]['pedigree']
                self.commit()


    def get_trending(self, sample_id = None, days = None):
        trending_doc = trending.prepare_trending(sample_id)
        return trending_doc

        """Find a case in the database by case id."""
        trending_obj = None
        trending_call = copy.deepcopy(self.base_call)

        if sample_id:
            trending_call.extend(['prepare-trending', '-s', sample_id])
        elif days:
            trending_call.extend(['prepare-trending', '-d', days])

        try:
            output = subprocess.check_output(
                ' '.join(trending_call),
                shell=True
            )
        except CalledProcessError:
            # If CalledProcessError is raised, log and raise error
            log_msg = f"Could not run command: {' '.join(trending_call)}"
            LOG.critical(log_msg)
            raise

        output = output.decode('utf-8')

        # If sample not in genotype db, stdout of genotype command will be empty.
        if not output:
            raise CaseNotFoundError(f"samples not found in genotype db")

        trending_obj = json.loads(output)[0]

        return trending_obj
