"""Hold sbatch templates in global variables"""

SBATCH_HEADER_TEMPLATE = """#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --account={account}
#SBATCH --ntasks={ntasks}
#SBATCH --mem={mem}G
#SBATCH --error={log_dir}/{job_name}.stderr
#SBATCH --output={log_dir}/{job_name}.stdout
#SBATCH --mail-type=FAIL
#SBATCH --mail-user={mail_user}
#SBATCH --time={time}:00:00
#SBATCH --qos=low

set -e

echo "Running on: $(hostname)"

source activate {conda_env}
"""

SBATCH_BAM_TO_CRAM = """
error() {{
    if [[ -e {cram_path} ]]
    then
        rm {cram_path}
    fi

    if [[ -e {cram_path}.crai ]]
    then
        rm {cram_path}.crai
    fi

    if [[ -e {pending_path} ]]
    then
        rm {pending_path}
    fi

    exit 1
}}

trap error ERR

touch {pending_path}
crunchy -r {reference_path} -t 12 compress bam -b {bam_path} -c {cram_path}
samtools quickcheck {cram_path}
touch {flag_path}
rm {pending_path}"""

######################################################################

SBATCH_FASTQ_TO_SPRING = """
error() {{
    if [[ -e {spring_path} ]]
    then
        rm {spring_path}
    fi

    if [[ -e {pending_path} ]]
    then
        rm {pending_path}
    fi

    exit 1
}}

trap error ERR

touch {pending_path}
crunchy -t 12 compress fastq -f {fastq_first} -s {fastq_second} -o {spring_path} --check-integrity \
--metadata-file
rm {pending_path}"""

SBATCH_SPRING_TO_FASTQ = """
error() {{
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

    exit 1
}}

trap error ERR

touch {pending_path}
crunchy -t 12 decompress spring {spring_path} -f {fastq_first} -s {fastq_second} \
--first-checksum {checksum_first} --second-checksum {checksum_second}
rm {pending_path}"""
