"""Hold sbatch templates in global variables"""

SBATCH_HEADER_TEMPLATE = """#! /bin/bash
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

mkdir -p {tmp_dir}
crunchy -t 12 --tmp-dir {tmp_dir} compress fastq -f {fastq_first} -s {fastq_second} \
-o {spring_path} --check-integrity --metadata-file
rm {pending_path}
rm -r {tmp_dir}"""

######################################################################

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

mkdir -p {tmp_dir}
crunchy -t 12 --tmp-dir {tmp_dir} decompress spring {spring_path} -f {fastq_first} -s \
{fastq_second} --first-checksum {checksum_first} --second-checksum {checksum_second}
rm {pending_path}
rm -r {tmp_dir}"""
