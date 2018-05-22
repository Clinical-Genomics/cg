import logging
from pathlib import Path

import ruamel.yaml

from cg.store import models, Store
from cg.apps.tb import TrailblazerAPI
from cg.apps.hk import HousekeeperAPI
from cg.exc import MissingAnalysisFileError

LOG = logging.getLogger(__name__)


class UploadStatsAPI():

    def __init__(self, status: Store, trailblazer: TrailblazerAPI, housekeeper: HousekeeperAPI):
        super(UploadStatsAPI, self).__init__()
        self.status = status
        self.trailblazer = trailblazer
        self.housekeeper = housekeeper

    def save_stats(self, analysis_obj: models.Analysis):
        """Save sample stats from an analysis."""
        hk_version = self.housekeeper.version(
            bundle=analysis_obj.family.internal_id,
            date=analysis_obj.started_at,
        )
        qcmetrics_query = self.housekeeper.files(version=hk_version.id, tags=['qcmetrics'])
        qcmetrics_file = qcmetrics_query.first()
        if not qcmetrics_file:
            raise MissingAnalysisFileError('qcmetrics')
        qcmetrics_path = Path(qcmetrics_file.full_path)
        if not qcmetrics_path.exists():
            raise MissingAnalysisFileError(qcmetrics_file.full_path)
        qcmetrics_raw = ruamel.yaml.safe_load(qcmetrics_path.open())
        qcmetrics_data = self.trailblazer.parse_qcmetrics(qcmetrics_raw)

        for sample_data in qcmetrics_data['samples']:
            LOG.debug(f"{sample_data['id']}: parse sample qc data")
            sample_obj = self.status.sample(sample_data['id'])
            if sample_obj is None:
                LOG.warning(f"{sample_data['id']}: sample not found")
                continue
            new_stats = self.parse(analysis_obj, sample_obj, sample_data)
            yield new_stats

    def parse(self, analysis: models.Analysis, sample: models.Sample,
              sample_qcmetrics: dict) -> models.SampleStats:
        """Build a database record for storing stats."""
        new_stats = self.status.add_samplestats(
            analysis=analysis,
            sample=sample,
            duplicates_percent=sample_qcmetrics['duplicates'],
            mapped_percent=sample_qcmetrics['mapped'],
            reads_total=sample_qcmetrics['reads'],
            strand_balance=sample_qcmetrics['strand_balance'],
            target_coverage=sample_qcmetrics['target_coverage'],
            completeness_target_10=sample_qcmetrics['completeness_target'][10],
            completeness_target_20=sample_qcmetrics['completeness_target'][20],
            completeness_target_50=sample_qcmetrics['completeness_target'][50],
            completeness_target_100=sample_qcmetrics['completeness_target'][100],
        )
        return new_stats

        # # variant calling
        # variants = Column(types.Integer)  # WHERE?
        # indels = Column(types.Integer)
        # snps = Column(types.Integer)
        # novel_sites = Column(types.Integer)  # WHERE?
        # concordant_rate = Column(types.Float)
        # hethom_ratio = Column(types.Float)
        # titv_ratio = Column(types.Float)

        # sample = orm.relationship(Sample, backref='stats', uselist=False)
        # analysis = orm.relationship(Analysis, backref='stats')
