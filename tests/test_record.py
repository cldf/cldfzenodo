import json
import logging

import pytest

from cldfzenodo.record import *


@pytest.fixture
def record_factory(fixtures_dir):
    def make_one(fname):
        return Record.from_dict(
            json.loads(fixtures_dir.joinpath(fname).read_text(encoding='utf8'))['hits']['hits'][0])
    return make_one


@pytest.fixture
def record(record_factory):
    return record_factory('record.json')


@pytest.mark.parametrize(
    'url_or_doi',
    [
        '10.5281/zenodo.5173799',
        "https://doi.org/10.5281/zenodo.5173799",
        "http://zenodo.org/doi/10.5281/zenodo.5173799",
        "https://zenodo.org/record/5173799",
        "https://zenodo.org/records/5173799",
    ]
)
def test_get_doi(url_or_doi):
    assert get_doi(url_or_doi) == '10.5281/zenodo.5173799'


def test_get_doi_error():
    with pytest.raises(ValueError):
        get_doi('http://example.com')


def test_GithubRepos():
    assert GithubRepos.from_url('http://example.com') is None
    repo = GithubRepos.from_url('https://github.com/org/repo')
    assert not repo.tag
    repo = GithubRepos.from_url('https://github.com/org/repo/tree/v1.0')
    assert repo.tag == 'v1.0'
    assert repo.clone_url
    assert repo.release_url


def test_Record(record):
    with pytest.raises(ValueError):
        _ = Record(doi='x', title='x')

    with pytest.raises(AssertionError):
        _ = Record(doi='10.5281/zenodo.4691101', title='')

    assert record.version == 'v1.1'
    assert record.concept_doi == '10.5281/zenodo.4691101'
    assert 'Greenhill, Simon J. and Haynie, Hannah J.' in record.bibtex
    assert record.metadata['resource_type']['type'] == 'dataset'

    rec = Record(doi='https://doi.org/10.5281/zenodo.4691101', title='', closed_access=True)
    assert rec.id == '4691101'


def test_Record_with_external_doi(record_factory):
    assert record_factory('record_with_external_doi.json')


def test_Record_multifile(record_factory, mocker, tmp_path):
    class Response:
        def __init__(self, *args):
            self.yielded = False
            self.code = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def read(self):
            return b'abc'

    rec = record_factory('record_multifile.json')
    assert len(rec.download_urls) == 5
    mocker.patch('cldfzenodo.api.urllib.request.urlopen', Response)
    assert len(list(rec.download(tmp_path / 'test').iterdir())) == 5


def test_Record_download_dataset(tmp_path, mocker, fixtures_dir, caplog, record):
    class Response:
        def __init__(self, *args):
            self.yielded = False
            self.code = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def read(self):
            return fixtures_dir.joinpath('petersonsouthasia-v1.1.zip').read_bytes()

    mocker.patch('cldfzenodo.api.urllib.request.urlopen', Response)

    with caplog.at_level(logging.INFO):
        assert record.download_dataset(tmp_path, log=logging.getLogger(__name__)).validate()
        assert caplog.records


def test_Record_citation(record, mocker):
    from cldfzenodo import API

    def urlopen(url):
        return mocker.Mock(
            read=lambda: "& The Citation".encode('utf8'))

    mocker.patch('cldfzenodo.api.urllib.request.urlopen', urlopen)
    assert record.get_citation(API) == '& The Citation'
