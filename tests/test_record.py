import html
import json
import logging
import zipfile

import pytest

from cldfzenodo.record import *


@pytest.fixture
def record(dcat_record_element):
    return Record.from_dcat_element(dcat_record_element)


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

    rec = Record(doi='https://doi.org/10.5281/zenodo.4691101', title='', closed_access=True)
    assert rec.id == '4691101'


def test_Record_from_dcat_multifile(dcat_record_element_multifile, mocker, tmp_path):
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

    rec = Record.from_dcat_element(dcat_record_element_multifile)
    assert len(rec.download_urls) == 5
    mocker.patch('cldfzenodo.record.urllib.request.urlopen', Response)
    assert len(list(rec.download(tmp_path / 'test').iterdir())) == 5


def test_Record_from_dcat(record):
    assert record.download_url


def test_Record_from_doi(mocker, dcat_record):
    def urlopen(url):
        if 'doi.org' in url:
            return mocker.Mock(url='http://zenodo.org/record/1234')
        return mocker.Mock(
            read=lambda: '<pre style="x">{}</pre>'.format(html.escape(dcat_record)).encode('utf8'))

    mocker.patch('cldfzenodo.record.urllib.request.urlopen', urlopen)
    rec = Record.from_doi('x')
    assert rec.id == '5173799'


def test_Record_from_concept_doi(mocker, tests_dir):
    def urlopen(url):
        content = json.loads(tests_dir.joinpath('search.json').read_text(encoding='utf8'))
        return mocker.Mock(read=lambda: json.dumps(content).encode('utf8'))

    mocker.patch('cldfzenodo.search.urllib.request.urlopen', urlopen)
    rec = Record.from_concept_doi('10.5281/zenodo.4691101', '1.1')
    assert rec.id == '5173799'


def test_DatasetResolver(mocker, tmp_path, tests_dir):
    from pycldf.ext.discovery import get_dataset

    class Record:
        def from_doi(self, doi):
            return self

        def download(self, d):
            with zipfile.ZipFile(tests_dir / 'petersonsouthasia-v1.1.zip', 'r') as zf:
                zf.extractall(d)
            return d

    mocker.patch('cldfzenodo.record.Record', Record())
    assert get_dataset('https://doi.org/10.5281/zenodo.1', tmp_path)
    assert get_dataset('https://zenodo.org/record/1', tmp_path)


def test_Record_download_dataset(tmp_path, mocker, tests_dir, caplog, record):
    class Response:
        def __init__(self, *args):
            self.yielded = False
            self.code = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def read(self):
            return tests_dir.joinpath('petersonsouthasia-v1.1.zip').read_bytes()

    mocker.patch('cldfzenodo.record.urllib.request.urlopen', Response)

    with caplog.at_level(logging.INFO):
        assert record.download_dataset(tmp_path, log=logging.getLogger(__name__)).validate()
        assert caplog.records


def test_Record_citation(record, mocker):
    def urlopen(url):
        return mocker.Mock(
            read=lambda: """
<h4>Cite as</h4>
  <div id="invenio-csl" class="ng-scope">    
    <invenio-csl ng-init="vm.citationResult = '&amp; The Citation'" class="ng-scope">
</div>
""".encode('utf8'))

    mocker.patch('cldfzenodo.record.urllib.request.urlopen', urlopen)
    assert record.citation == '& The Citation'
