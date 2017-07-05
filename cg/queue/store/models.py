# -*- coding: utf-8 -*-
import alchy
from sqlalchemy import Column, ForeignKey, orm, types

Model = alchy.make_declarative_base(Base=alchy.ModelBase)


class MipAnalysis(Model):
    has_fastqs = Column(types.Boolean, default=False)
    has_config = Column(types.Boolean, default=False)
    has_panel = Column(types.Boolean, default=False)
    started_at = Column(types.DateTime)
    finished_at = Column(types.DateTime)

    errors = Column(types.Text)

    scout_delivery = orm.relationship('ScoutDelivery', backref='mip_analysis', uselist=False)


class ScoutDelivery(Model):
    family_id = Column(types.String(64), nullable=False, unique=True)

    has_coverage = Column(types.Boolean, default=False)
    has_observations = Column(types.Boolean, default=False)
    has_delivery_report = Column(types.Boolean, default=False)
    has_config = Column(types.Boolean, default=False)

    errors = Column(types.Text)

    mip_analysis_id = Column(ForeignKey(MipAnalysis.id), ondelete='CASCADE', nullable=False)


class Genotypes(Model):
    # I want genotypes for sample:
    sample_id = Column(types.String(64), nullable=False, unique=True)

    # ... for that I need a:
    bcf_file = Column(types.Text)

    # ... for that I need an analysis in Housekeeper:
    bundle_version_id = Column(types.Integer)

    # ... for that I need to start an analysis:
    mip_analysis_id = Column(ForeignKey(MipAnalysis.id), ondelete='CASCADE')



# coverage, observations, genotypes, qc stats
