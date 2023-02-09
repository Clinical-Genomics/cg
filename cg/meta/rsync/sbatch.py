"""Sbatch templates for the rsync function"""

RSYNC_COMMAND = """
rsync -rvpL {source_path} {destination_path}
"""

RSYNC_CONTENTS_COMMAND = """
rsync -rvpL {source_path}/ {destination_path}
"""

COVID_RSYNC = """
rsync -rvptL {source_path} {destination_path}
rsync -rvptL --chmod=777 {covid_report_path} {covid_destination_path}
"""

ERROR_RSYNC_FUNCTION = """
echo "Rsync failed"
"""
