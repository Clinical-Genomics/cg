# -*- coding: utf-8 -*-
from sqlalchemy import and_, or_

from cg.store import models


class StatusHandler:

    def families_to_analyze(self):
        """Fetch families without analyses where all samples are sequenced."""
        records = (
            self.Family.query
            .outerjoin(models.Family.analyses)
            .join(models.Family.links, models.FamilySample.sample)
            .filter(or_(
                models.Family.analyze == True,
                and_(
                    models.Sample.sequenced_at != None,
                    models.Analysis.analyzed_at == None
                )
            ))
        )
        return records

    def families_to_upload(self):
        """Fetch analyses that haven't been uploaded."""
        records = self.Analysis.filter(models.Analysis.analyzed_at != None,
                                       models.Analysis.uploaded_at == None)
        return records

    def families_to_deliver(self):
        """Fetch analyses that have been uploaded but not delivered."""
        records = self.Analysis.filter(models.Analysis.uploaded_at != None,
                                       models.Analysis.delivered_at == None)
        return records

    def samples_to_deliver(self):
        """Fetch samples that have been sequenced but not delivered."""
        records = self.Sample.filter(models.Sample.sequenced_at != None,
                                     models.Sample.delivered_at == None)
        return records
