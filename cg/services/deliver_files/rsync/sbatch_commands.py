"""Sbatch templates for the rsync function"""

CREATE_INBOX_COMMAND = """
ssh {host} "mkdir -p {inbox_path}"
"""

RSYNC_COMMAND = """
rsync -rvL {source_path} {destination_path}
"""

RSYNC_CONTENTS_COMMAND = """
rsync -rvL {source_path}/ {destination_path}
"""

COVID_RSYNC = """
rsync -rvL {source_path} {destination_path}
rsync -rvL --chmod=777 {covid_report_path} {covid_destination_path}
"""

COVID_REPORT_RSYNC = """
rsync -rvL --chmod=777 {covid_report_path} {covid_destination_path}
"""

ERROR_CREATE_INBOX_FUNCTION = """
echo "Create inbox failed"
"""

ERROR_RSYNC_FUNCTION = """
echo "Rsync failed"
"""
