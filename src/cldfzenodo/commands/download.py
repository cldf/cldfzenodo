"""
Download a CLDF dataset from Zenodo
"""
import pathlib

from clldutils.clilib import PathType

from cldfzenodo import Record


def register(parser):
    parser.add_argument('doi')
    parser.add_argument(
        '--directory',
        type=PathType(type='dir', must_exist=False),
        default=pathlib.Path('.'),
    )


def run(args):
    Record.from_doi(args.doi).download_dataset(args.directory)
