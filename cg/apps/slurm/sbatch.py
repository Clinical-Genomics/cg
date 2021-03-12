SBATCH_HEADER_TEMPLATE = """#! /bin/bash
#SBATCH --job-name={job_name}
#SBATCH --account={account}
#SBATCH --ntasks={number_tasks}
#SBATCH --mem={memory}G
#SBATCH --error={log_dir}/{job_name}.stderr
#SBATCH --output={log_dir}/{job_name}.stdout
#SBATCH --mail-type=FAIL
#SBATCH --mail-user={email}
#SBATCH --time={hours}:{minutes}:00
#SBATCH --qos={priority}

set -eu -o pipefail

log() {{
    NOW=$(date +"%Y%m%d%H%M%S")
    echo "[${{NOW}}] $*"
}}

log "Running on: $(hostname)"
"""

# Double {{ to escape this character
SBATCH_BODY_TEMPLATE = """
error() {{
    {error_body}
    exit 1
}}

trap error ERR

{commands}

"""
