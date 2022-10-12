"""
Download a CLDF dataset from Zenodo
"""
import pathlib

from clldutils.clilib import PathType

from cldfzenodo import Record


def register(parser):
    parser.add_argument(
        'doi',
        help="DOI of the dataset, starting with 10.5281, Zenodo's DOI prefix.")
    parser.add_argument(
        '--directory',
        type=PathType(type='dir', must_exist=False),
        default=pathlib.Path('.'),
    )


def run(args):
    Record.from_doi(args.doi).download_dataset(args.directory)
