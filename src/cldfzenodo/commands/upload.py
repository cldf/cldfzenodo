"""
Upload files for a Zenodo deposit.

While the GitHub-Zenodo integration is useful for CLDF datasets, it is not practical for large
amounts of media files. In such cases, media files can be put into a separate Zenodo deposit and
linked to the CLDF dataset using MediaTable's "Download_URL and Path_In_Zip" mechanism.

This command helps in this scenario as follows:
1. Create a new deposit on Zenodo (using a user account for which an ACCESS TOKEN with suitable
   scope is available.)
2. Package the media files into zip files in one directory.
3. Run this command passing
   - the directory containing the zip files
   - the (7-digit) deposit ID
   - the ACCESS TOKEN
"""
import os
import json

import requests
from clldutils.clilib import PathType

from cldfzenodo.api import API


def register(parser):
    parser.add_argument(
        'deposit_id',
        help='7-digit ID of the deposit',
    )
    parser.add_argument(
        'upload_dir',
        type=PathType(type='dir'),
        help='Directory holding the files to upload',
    )
    parser.add_argument(
        'access_token',
        help="Name of the environment variable holding the Zenodo ACCESS TOKEN for the requests.",
    )


def run(args):
    r = API(
        'deposit/depositions',
        id_=args.deposit_id,
        params={'access_token': os.environ.get(args.access_token)},
        headers={"Content-Type": "application/json"})
    bucket_url = json.loads(r)['links']['bucket']

    for p in args.upload_dir.iterdir():
        if p.is_file():
            r = requests.put(
                '%s/%s' % (bucket_url, p.name),
                data=p.open('rb'),
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {os.environ.get(args.access_token)}",
                    "Content-Type": "application/octet-stream"}
            )
            args.log.info('%s\tHTTP %s', p.name, r.status_code)
