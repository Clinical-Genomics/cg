WORKFLOW_TEMPLATE = """#! /bin/bash
#SBATCH --job-name={job_name}
#SBATCH --account={account}
#SBATCH --ntasks={number_tasks}
#SBATCH --mem={memory}G
#SBATCH --error={output_fastq_dir}/{job_name}.stderr
#SBATCH --output={output_fastq_dir}/{job_name}.stdout
#SBATCH --mail-type=ALL
#SBATCH --mail-user={email}
#SBATCH --time={time}
#SBATCH --qos={quality_of_service}

set -eu -o pipefail
log() {{
    NOW=$(date +"%Y-%m-%dT%H:%M:%S")
    echo "[${{NOW}}] $*" 1>&2;
}}
log "Running on: $(hostname)"

log "Executing: {bin_downsample} {input_fastq_dir}/ {output_fastq_dir}/ {downsample_to} {original_sample_reads}"
{bin_downsample} {input_fastq_dir}/ {output_fastq_dir}/ {downsample_to} {original_sample_reads}
"""
