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
        help='Output directory (will be created if it does not exist).',
        type=PathType(type='dir', must_exist=False),
        default=pathlib.Path('.'),
    )
    parser.add_argument(
        '--version-tag',
        help="If DOI is a concept DOI (see https://help.zenodo.org/#versioning), a version tag "
             "can be specified to select a particular version of the dataset (rather than the "
             "latest one).",
        default=None,
    )
    parser.add_argument(
        '--full-deposit',
        action='store_true',
        default=False,
        help='Download all files of the deposit (rather than just the CLDF dataset).',
    )


def run(args):
    rec = Record.from_concept_doi(args.doi, args.version_tag) \
        if args.version_tag else Record.from_doi(args.doi)
    rec.download(args.directory) if args.full_deposit else rec.download_dataset(args.directory)
