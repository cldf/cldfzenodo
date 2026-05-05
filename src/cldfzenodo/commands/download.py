"""
Download a CLDF dataset from Zenodo
"""

import pathlib

from clldutils.clilib import PathType

from cldfzenodo.api import API


def register(parser):  # pylint: disable=C0116
    parser.add_argument(
        "doi", help="DOI of the dataset, starting with 10.5281, Zenodo's DOI prefix."
    )
    parser.add_argument(
        "--directory",
        help="Output directory (will be created if it does not exist).",
        type=PathType(type="dir", must_exist=False),
        default=pathlib.Path("."),
    )
    parser.add_argument(
        "--version-tag",
        help="If DOI is a concept DOI (see https://help.zenodo.org/#versioning), a version tag "
        "can be specified to select a particular version of the dataset (rather than the "
        "latest one).",
        default=None,
    )
    parser.add_argument(
        "--full-deposit",
        action="store_true",
        default=False,
        help="Download all files of the deposit (rather than just the CLDF dataset).",
    )


def run(args):  # pylint: disable=C0116
    if args.version_tag:
        rec = API.get_record(conceptdoi=args.doi, version=args.version_tag)
    else:
        rec = API.get_record(doi=args.doi)
    if not rec:
        raise ValueError("No record found")  # pragma: no cover
    if args.full_deposit:
        rec.download(args.directory)
    else:
        rec.download_dataset(args.directory)
    return 0
