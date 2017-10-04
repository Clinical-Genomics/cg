# -*- coding: utf-8 -*-
import codecs
import os.path
import subprocess
from tempfile import NamedTemporaryFile, mkdtemp
from typing import List

SEX_GENDER = {'male': 'M', 'female': 'F'}
COLUMNS = {
    'family': 'FamilyId',
    'sample': 'IndividualId',
    'sex': 'Gender',
    'father': 'father',
    'mother': 'mother',
    'deceased': 'Deceased',
    'proband': 'Proband',
    'affected': 'Affected',
}


def make_ped(family_id: str, samples: List[dict]):
    """Make Madeline pedigree file."""
    yield from COLUMNS.values()
    for sample in samples:
        row = [
            family_id,
            sample['sample'],
            SEX_GENDER.get(sample['sex'], '.'),
            sample.get('father', '.'),
            sample.get('mother', '.'),
            'Y' if sample.get('deceased') else '.',
            'Y' if sample.get('proband') else '.',
            'Y' if sample.get('affected') else '.',
        ]
        yield ' '.join(row)


def run(executable: str, ped_stream: List[str]):
    """Run madeline and generate a file with the results."""
    madeline_exe = os.path.abspath(executable)
    output_dir = mkdtemp()
    output_prefix = f"{output_dir}/madeline"
    out_path = f"{output_prefix}.xml"

    # write the input to a temp file
    with NamedTemporaryFile('r+w') as in_file:
        madeline_content = '\n'.join(ped_stream)
        in_file.write(madeline_content)
        in_file.flush()
        subprocess.call([madeline_exe, '--color', '--outputprefix',
                         output_prefix, in_file.name])

    with codecs.open(out_path, 'r') as output:
        svg_content = output.read()

    # strip away the script tag
    script_tag = ('<script type="text/javascript" xlink:href='
                  '"javascript/madeline.js"></script>')
    svg_content.replace(script_tag, '')

    with open(out_path, 'w') as out_handle:
        out_handle.write(svg_content)

    return out_path
