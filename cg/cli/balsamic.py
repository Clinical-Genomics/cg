""" Add CLI support to start BALSAMIC """
import gzip
import logging
import re
import subprocess
from pathlib import Path

import click
from cg.apps import hk
from cg.apps.balsamic.fastq import BalsamicFastqHandler
from cg.meta.analysis import AnalysisAPI
from cg.store import Store

LOGGER = logging.getLogger(__name__)
SUCCESS = 0


@click.group()
@click.pass_context
def balsamic(context):
    """ Run cancer workflow """


@balsamic.command()
@click.option('-d', '--dry', is_flag=True, help='print config to console')
@click.option('--target-bed', required=False, help='Optional')
@click.option('--umi-trim-length', default=5, required=False, help='Default 5')
@click.option('--quality-trim', is_flag=True, required=False, help='Optional')
@click.option('--adapter-trim', is_flag=True, required=False, help='Optional')
@click.option('--umi', is_flag=True, required=False, help='Optional')
@click.argument('case_id')
@click.pass_context
def config(context, dry, target_bed, umi_trim_length, quality_trim, adapter_trim,
           umi, case_id):
    """Generate a config for the case_id.
    """

    # missing sample_id and files
    case_obj = Store(context.obj['database']).family(case_id)
    link_objs = case_obj.links
    tumor_paths = set()
    normal_paths = set()
    singularity = context.obj['balsamic']['singularity']
    reference_config = context.obj['balsamic']['reference_config']
    conda_env = context.obj['balsamic']['conda_env']
    root_dir = context.obj['balsamic']['root']
    wrk_dir = Path(f'{root_dir}/{case_id}/fastq')
    for link_obj in link_objs:
        LOGGER.info("%s: config FASTQ file", link_obj.sample.internal_id)

        linked_reads_paths = {1: [], 2: []}
        concatenated_paths = {1: '', 2: ''}

        file_objs = hk.HousekeeperAPI(context.obj).files(bundle=link_obj.sample.internal_id,
                                                         tags=['fastq'])
        files = []
        for file_obj in file_objs:
            # figure out flowcell name from header
            with gzip.open(file_obj.full_path) as handle:
                header_line = handle.readline().decode()
                header_info = AnalysisAPI._fastq_header(header_line)

            data = {
                'path': file_obj.full_path,
                'lane': int(header_info['lane']),
                'flowcell': header_info['flowcell'],
                'read': int(header_info['readnumber']),
                'undetermined': ('_Undetermined_' in file_obj.path),
            }
            # look for tile identifier (HiSeq X runs)
            matches = re.findall(r'-l[1-9]t([1-9]{2})_', file_obj.path)
            if len(matches) > 0:
                data['flowcell'] = f"{data['flowcell']}-{matches[0]}"
            files.append(data)

        sorted_files = sorted(files, key=lambda k: k['path'])

        for fastq_data in sorted_files:
            original_fastq_path = Path(fastq_data['path'])
            linked_fastq_name = BalsamicFastqHandler.FastqFileNameCreator.create(
                lane=fastq_data['lane'],
                flowcell=fastq_data['flowcell'],
                sample=link_obj.sample.internal_id,
                read=fastq_data['read'],
                more={'undetermined': fastq_data['undetermined']},
            )
            concatenated_fastq_name = \
                BalsamicFastqHandler.FastqFileNameCreator.get_concatenated_name(
                    linked_fastq_name)

            linked_fastq_path = wrk_dir / linked_fastq_name

            linked_reads_paths[fastq_data['read']].append(linked_fastq_path)
            concatenated_paths[fastq_data['read']] = f"{wrk_dir}/{concatenated_fastq_name}"

            if linked_fastq_path.exists():
                LOGGER.info("found: %s -> %s", original_fastq_path, linked_fastq_path)
            else:
                LOGGER.debug("destination path already exists: %s", linked_fastq_path)

        if link_obj.sample.is_tumour:
            tumor_paths.add(concatenated_paths[1])
        else:
            normal_paths.add(concatenated_paths[1])

    nr_paths = len(tumor_paths) if tumor_paths else 0
    if nr_paths != 1:
        click.echo("Must have exactly one tumor sample! Found {nr_paths} samples.", color="red")
        context.abort()

    tumor_path = tumor_paths.pop()

    normal_path = None
    nr_normal_paths = len(normal_paths) if normal_paths else 0
    if nr_normal_paths > 1:
        click.echo(f"Too many normal samples found: {nr_normal_paths}", color="red")
        context.abort()
    elif nr_normal_paths == 1:
        normal_path = normal_paths.pop()

    # Call Balsamic
    command_str = (f"config case "
                   f"--reference-config {reference_config}"
                   f" --singularity {singularity} "
                   f"--tumor {tumor_path} "
                   f"--case-id {case_id} "
                   f"--output-config {case_id}.json "
                   f"--analysis-dir {root_dir} "
                   f"--umi-trim-length {umi_trim_length}")

    if target_bed:
        command_str += f" -p {target_bed} "
    if normal_path:
        command_str += f" --normal {normal_path} "
    if umi:
        command_str += f" --umi "
    if quality_trim:
        command_str += f" --quality-trim "
    if adapter_trim:
        command_str += f" --adapter-trim "

    command = [f"bash -c 'source activate {conda_env}; balsamic"]
    command_str += "'"  # add ending quote from above line
    command.extend(command_str.split(' '))

    if dry:
        print(' '.join(command))
        return SUCCESS
    else:
        process = subprocess.run(
            ' '.join(command), shell=True
        )
        return process


@balsamic.command()
@click.option('-d', '--dry', is_flag=True, help='print command to console')
@click.option('-r', '--run-analysis', is_flag=True, default=False, help='start analysis')
@click.option('--config', 'config_path', required=False, help='Optional')
@click.option('--analysis-type', 'analysis_type', required=False, default='qc', help='Optional')
@click.option('-p', '--priority', type=click.Choice(['low', 'normal', 'high']))
@click.option('-e', '--email', help='email to send errors to')
@click.argument('case_id')
@click.pass_context
def run(context, dry, run_analysis, config_path, analysis_type, priority, email, case_id):
    """Generate a config for the case_id."""

    conda_env = context.obj['balsamic']['conda_env']
    slurm_account = context.obj['balsamic']['slurm']['account']
    priority = priority if priority else context.obj['balsamic']['slurm']['qos']
    root_dir = Path(context.obj['balsamic']['root'])
    if not config_path:
        config_path = Path.joinpath(root_dir, case_id, case_id + '.json')

    # Call Balsamic
    command_str = (f" run analysis "
                   f"--slurm-account {slurm_account}"
                   f"-s {config_path} ")

    if run_analysis:
        command_str += " --run-analysis "

    if email:
        command_str += f" --slurm-mail-user {email} "

    command_str += f" --qos {priority} "

    command = [f"bash -c 'source activate {conda_env}; balsamic"]
    command_str += "'"
    command.extend(command_str.split(' '))

    if dry:
        print(' '.join(command))
    else:
        process = subprocess.run(
            ' '.join(command), shell=True
        )
        return process
