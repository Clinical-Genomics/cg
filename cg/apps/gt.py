# -*- coding: utf-8 -*-
import logging

from genotype.store import api
from genotype.store.parsemip import parse_mipsex
from genotype.load.vcf import load_vcf

import ruamel.yaml

log = logging.getLogger(__name__)


def connect(config):
    """Connect to the Housekeeper database."""
    genotype_db = api.connect(config['genotype']['database'])
    return genotype_db


def add(genotype_db, raw_bcf_path, force=False):
    """Add genotypes for an analysis run."""
    snps = api.snps()
    analyses = load_vcf(raw_bcf_path, snps)
    for analysis in analyses:
        log.debug('loading VCF genotypes for sample: %s', analysis.sample_id)
        is_saved = api.add_analysis(genotype_db, analysis, replace=force)
        if is_saved:
            log.info('loaded VCF genotypes for sample: %s', analysis.sample_id)
        else:
            log.warn('skipped, found previous analysis: %s', analysis.sample_id)


def add_sex(genotype_db, samples_sex, qcmetrics_stream):
    """Add missing sex information to samples."""
    qcm_data = ruamel.yaml.safe_load(qcmetrics_stream)
    mip_samples_sex = parse_mipsex(qcm_data)
    for sample_id, mip_sex in mip_samples_sex.items():
        genotype_sample = api.sample(sample_id)
        log.info("marking %s as %s", sample_id, samples_sex[sample_id])
        genotype_sample.sex = samples_sex[sample_id]
        genotype_analysis = api.analysis(sample_id, 'sequence').first()
        log.info("marking analysis for %s as %s", sample_id, mip_sex)
        genotype_analysis.sex = mip_sex

    genotype_db.commit()

# {
#     local sample=${1?'missing input - sample name'};
#     local qc_metrics;
#     if qc_metrics=$(housekeeper get --sample "${sample}" --infer-\case --category qc); then
#         local sample_sex=$(cglims get "${sample}" sex);
#         local sequence_sex=$(genotype mip-sex --sample "${sample}" "${qc_metrics}");
#         if [[ -z "${sample_sex}" || -z "${sequence_sex}" ]]; then
#             ( echo "sample sex information missing: ${sample}" 1>&2 );
#             return 1;
#         else
#             genotype add-sex --sample "${sample_sex}" --analysis sequence "${sequence_sex}" "${sample}";
#         fi;
#     else
#         ( echo "can't find QC metrics for: ${sample}" 1>&2 );
#         return 1;
#     fi;
#     return 0
# }
