from pathlib import Path

from cg.services.fastq_service.utils import concatenate_forward_reads, concatenate_reverse_reads


class FastqService:

    def concatenate(self, fastq_directory: Path, forward_output: Path, reverse_output: Path):
        concatenate_forward_reads(directory=fastq_directory, output_file=forward_output)
        concatenate_reverse_reads(directory=fastq_directory, output_file=reverse_output)
