SBATCH_HEADER_TEMPLATE = """#! /bin/bash {use_login_shell}
#SBATCH --job-name={job_name}
#SBATCH --account={account}
#SBATCH --ntasks={number_tasks}
#SBATCH --mem={memory}G
#SBATCH --error={log_dir}/{job_name}.stderr
#SBATCH --output={log_dir}/{job_name}.stdout
#SBATCH --mail-type=FAIL
#SBATCH --mail-user={email}
#SBATCH --time={hours}:{minutes}:00
#SBATCH --qos={quality_of_service}
{optional_headers}

set -eu -o pipefail

log() {{
    NOW=$(date +"%Y-%m-%dT%H:%M:%S")
    echo "[${{NOW}}] $*" 1>&2;
}}

log "Running on: $(hostname)"
"""

DRAGEN_SBATCH_HEADER_TEMPLATE = """#! /bin/bash -l
#SBATCH --job-name={job_name}
#SBATCH --partition={partition}
#SBATCH --account={account}
#SBATCH --exclusive
#SBATCH --mem=0 # Allocates all memory on the node
#SBATCH --error={log_dir}/{job_name}.stderr
#SBATCH --output={log_dir}/{job_name}.stdout
#SBATCH --mail-type=FAIL
#SBATCH --mail-user={email}
#SBATCH --time={hours}:{minutes}:00
#SBATCH --qos={quality_of_service}

set -eu -o pipefail

ulimit -n 65535
ulimit -u 16384

export PATH=$PATH:/opt/edico/bin

log() {{
    NOW=$(date +"%Y-%m-%dT%H:%M:%S")
    echo "[${{NOW}}] $*" 1>&2;
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
