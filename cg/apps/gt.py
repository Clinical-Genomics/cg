# -*- coding: utf-8 -*-
import logging

from alchy import Manager
from genotype.store import api, models, vogue
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
        trending_doc = vogue.prepare_trending(sample_id)
        return trending_doc
