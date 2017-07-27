# -*- coding: utf-8 -*-
import logging
import io
from pathlib import Path

from chanjo.store.api import ChanjoDB
from chanjo.load.sambamba import load_transcripts
import click
from sqlalchemy.exc import IntegrityError

log = logging.getLogger(__name__)


class ChanjoAPI(ChanjoDB):

    def __init__(self, config: dict):
        super(ChanjoAPI, self).__init__(uri=config['chanjo']['database'])

    def upload(self, sample_id: str, sample_name: str, group_id: str, group_name: str,
               bed_stream: io.TextIOWrapper):
        source = str(Path(bed_stream.name).absolute())
        result = load_transcripts(bed_stream, sample_id=sample_id, group_id=group_id,
                                  source=source, threshold=10)

        result.sample.name = sample_name
        result.sample.group_name = group_name

        try:
            self.add(result.sample)
            with click.progressbar(result.models, length=result.count,
                                   label='loading transcripts') as progress_bar:
                for tx_model in progress_bar:
                    self.add(tx_model)
            self.save()
        except IntegrityError as error:
            self.session.rollback()
            raise error
