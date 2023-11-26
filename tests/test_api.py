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


def test_Api_get_github_release_info(mocker):
    class Subprocess:
        @staticmethod
        def check_output(cmd):
            if 'list' in cmd:
                return b"""TITLE                   TYPE    TAG NAME  PUBLISHED         
Glottolog Database 4.8  Latest  v4.8      about 4 months ago"""
            return """v4.8
xrotwang released this about 4 months ago

  Hammarström, Harald & Forkel, Robert & Haspelmath, Martin & Bank, Sebastian. 2023. Glottolog 4.8. Leipzig: Max      
  Planck Institute for Evolutionary Anthropology. (Available online at https://glottolog.org/)                        
                                                                                                                      
  DOI https://doi.org/10.5281/zenodo.8131084                                                                          


View on GitHub: https://github.com/glottolog/glottolog/releases/tag/v4.8""".encode('utf8')

    class Response:
        def __init__(self, what):
            self.what = what

        def read(self):
            if self.what == 'apa':
                return b'The Citation'
            return (' @misc{harald hammarström_robert forkel_martin haspelmath_sebastian bank_2023, '
                    'title={glottolog/glottolog: Glottolog database 4.8}, '
                    'DOI={10.5281/zenodo.8131084}, '
                    'abstractNote={Hammarström, Harald & Forkel, Robert & Haspelmath, Martin & Bank, Sebastian. 2023. Glottolog 4.8. Leipzig: Max Planck Institute for Evolutionary Anthropology. (Available online at https://glottolog.org)}, '
                    'publisher={Zenodo}, '
                    'author={Harald Hammarström and Robert Forkel and Martin Haspelmath and Sebastian Bank}, '
                    'year={2023}, '
                    'month={Jul} }').encode('utf8')

    def urlopen(req):
        if 'style=apa' in req.full_url:
            return Response('apa')
        return Response('bibtex')

    mocker.patch('cldfzenodo.api.subprocess', Subprocess())
    mocker.patch('cldfzenodo.api.urllib.request.urlopen', urlopen)

    tag, doi, cit, bib = Api().get_github_release_info('glottolog/glottolog', bibid='x')
    assert tag == 'v4.8'
    assert doi == '10.5281/zenodo.8131084'
    assert cit == 'The Citation'
    assert bib.id == 'x'
