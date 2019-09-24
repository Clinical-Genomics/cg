# -*- coding: utf-8 -*-
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


@click.group()
@click.pass_context
def balsamic(context):
    context.obj['hk'] = hk.HousekeeperAPI(context.obj)
    context.obj['db'] = Store(context.obj['database'])


@balsamic.command()
@click.option('-d', '--dry', is_flag=True, help='print config to console')
@click.option('--target-bed', required=False, help='Optional')
@click.argument('case_id')
@click.pass_context
def config(context, dry, target_bed, case_id):
    """Generate a config for the case_id.
    """

    # missing sample_id and files
    case_obj = context.obj['db'].family(case_id)
    link_objs = case_obj.links

    for link_obj in link_objs:
        LOGGER.info("%s: link FASTQ files", link_obj.sample.internal_id)
        root_dir = context.obj['balsamic']['root']
        wrk_dir = Path(f'{root_dir}/{case_id}/fastq')

        linked_reads_paths = {1: [], 2: []}
        concatenated_paths = {1: '', 2: ''}

        file_objs = context.obj['hk'].files(bundle=link_obj.sample.internal_id, tags=['fastq'])
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
            tumor_path = concatenated_paths[1]
        else:
            normal_path = concatenated_paths[1]

    if not tumor_path:
        click.echo("No tumor found!", color="red")
        raise

    # Call Balsamic
    command_str = (f"config case "
                   f"--reference-config "
                   f"/home/proj/production/cancer/reference/GRCh37/reference.json "
                   f"--tumor {tumor_path} "
                   f"--case-id {case_id} "
                   f"--output-config {case_id}.json "
                   f"--analysis-dir {root_dir}")
    if target_bed:
        command_str += f" -p {target_bed} "

    if normal_path:
        command_str += f"--normal {normal_path}"

    command = ["bash -c 'source activate P_BALSAMIC-base_3.0.1; balsamic"]
    command_str += "'" # add ending quote from above line
    command.extend(command_str.split(' '))

    if dry:
        print(' '.join(command))
    else:
        process = subprocess.run(
            ' '.join(command), shell=True
        )
        return process


@balsamic.command()
@click.option('-d', '--dry', is_flag=True, help='print config to console')
@click.option('--config', 'config_path', required=False, help='Optional')
@click.argument('case_id')
@click.pass_context
def run(context, dry, config_path, case_id):
    """Generate a config for the case_id.
    """

    root_dir = Path(context.obj['balsamic']['root'])
    if not config_path:
        config_path = Path.joinpath(root_dir, case_id, case_id + '.json')

    # Call Balsamic
    # TODO: Analysis type as option
    # TODO: slurm-account as option
    command_str = (f" run analysis "
                   f"--run-analysis --slurm-account development "
                   f"-s {config_path} ")

    command_str += "'"

    command = ["bash -c 'source activate P_BALSAMIC-base_3.0.1; balsamic"]
    command.extend(command_str.split(' '))

    if dry:
        print(' '.join(command))
    else:
        process = subprocess.run(
            ' '.join(command), shell=True
        )
        return process
