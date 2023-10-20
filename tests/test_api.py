import zipfile

import pytest

from cldfzenodo.api import Api


def test_DatasetResolver(mocker, tmp_path, fixtures_dir):
    from pycldf.ext.discovery import get_dataset

    class Record:
        def download(self, d):
            with zipfile.ZipFile(fixtures_dir / 'petersonsouthasia-v1.1.zip', 'r') as zf:
                zf.extractall(d)
            return d

    class API:
        def get_record(self, *args, **kw):
            return Record()

    mocker.patch('cldfzenodo.api.API', API())
    assert get_dataset('https://doi.org/10.5281/zenodo.1', tmp_path)
    assert get_dataset('https://zenodo.org/record/1', tmp_path)
    assert tmp_path.joinpath('cldf-datasets-petersonsouthasia-e029fbf').exists()


def test_Api_iter_records(urlopen, mocker):
    mocker.patch('cldfzenodo.api.urllib.request.urlopen', urlopen)
    res = Api(page_size=10).iter_records(allversions=True)
    recs = []
    for i in range(15):
        recs.append(next(res))
    assert len(recs) == 15
    assert len({r.doi for r in recs}) == 10, "Should only get 10 different records"

    res = list(Api().iter_records(community='lexibank'))
    assert len(res) == 10

    res = list(Api().iter_records(keyword='x'))
    assert len(res) == 10


def test_Api_get_record(urlopen, mocker):
    mocker.patch('cldfzenodo.api.urllib.request.urlopen', urlopen)

    rec = Api().get_record(doi='10.5281/zenodo.5173799')
    assert rec.doi == '10.5281/zenodo.5173799'

    rec = Api().get_record(conceptdoi='10.5281/zenodo.5173799')
    assert rec.doi == '10.5281/zenodo.5173799'

    assert Api().get_record(conceptdoi='10.5281/zenodo.5173799', version='y') is None
    assert Api().get_record(conceptdoi='10.5281/zenodo.5173799', version='v1.1') is not None

    assert list(Api().iter_versions('10.5281/zenodo.5173799'))
