"""Hold sbatch templates in global variables"""

FASTQ_TO_SPRING_ERROR = """
if [[ -e {spring_path} ]]
then
    rm {spring_path}
fi

if [[ -e {pending_path} ]]
then
    rm {pending_path}
fi
"""

SPRING_TO_FASTQ_ERROR = """
if [[ -e {fastq_first} ]]
then
    rm {fastq_first}
fi

if [[ -e {fastq_second} ]]
then
    rm {fastq_second}
fi

if [[ -e {pending_path} ]]
then
    rm {pending_path}
fi
"""

FASTQ_TO_SPRING_COMMANDS = """
mkdir -p {tmp_dir}
{conda_run} crunchy -t 12 --tmp-dir {tmp_dir} compress fastq -f {fastq_first} -s {fastq_second} \
-o {spring_path} --check-integrity --metadata-file
rm {pending_path}
rm -r {tmp_dir}
"""

SPRING_TO_FASTQ_COMMANDS = """
mkdir -p {tmp_dir}
{conda_run} crunchy -t 12 --tmp-dir {tmp_dir} decompress spring {spring_path} -f {fastq_first} -s \
{fastq_second} --first-checksum {checksum_first} --second-checksum {checksum_second}
rm {pending_path}
rm -r {tmp_dir}
"""
