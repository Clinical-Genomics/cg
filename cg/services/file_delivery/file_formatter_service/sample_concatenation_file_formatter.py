from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)


class SampleConcatenationFileFormatter:
    def __init__(self, concatenation_service: FastqConcatenationService):
        self.concatenation_service = concatenation_service
