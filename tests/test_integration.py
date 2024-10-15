import pytest

from cldfzenodo.api import Api


@pytest.fixture(scope='session')
def API():  # pragma: no cover
    class CountingApi(Api):
        def __init__(self, *args, **kw):
            Api.__init__(self, *args, **kw)
            self.total_requests = 0
            self.scoped_requests = 0

        def __call__(self, *args, **kw):
            self.total_requests += 1
            self.scoped_requests += 1
            kw['_verbose'] = True
            return Api.__call__(self, *args, **kw)

        def __enter__(self):
            self.scoped_requests = 0
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    return CountingApi(page_size=5)


def get_10(iterator):  # pragma: no cover
    res = []
    for i in range(10):
        res.append(next(iterator))
    return res


@pytest.mark.integration
def test_communities(API):  # pragma: no cover
    with API:
        res = get_10(API.iter_records(community='cldf-datasets'))
    print(res[0].communities)
    print(res[0].doi)
    assert len(res) == 10
    assert all('cldf-datasets' in r.communities for r in res), res[0].communities
    assert len({r.doi for r in res}) == 10
    assert API.scoped_requests == 3


@pytest.mark.integration
def test_keyword(API):  # pragma: no cover
    with API:
        res = get_10(API.iter_records(keyword='cldf:Generic'))
    assert len(res) == 10
    assert all('cldf:Generic' in r.keywords for r in res)
    assert len({r.doi for r in res}) == 10
    assert API.scoped_requests == 2


@pytest.mark.integration
def test_record(API):  # pragma: no cover
    with API:
        rec = API.get_record(doi="10.5281/zenodo.5173799")
        cit = rec.get_citation(API)
    assert rec.id == '5173799'
    assert 'Greenhill' in cit
    assert API.scoped_requests == 2

    rec1 = API.get_record(conceptdoi="10.5281/zenodo.4691101", version="v1.1")
    assert rec1.version == 'v1.1'
    assert rec1.concept_doi == "10.5281/zenodo.4691101"

    rec2 = API.get_record(conceptdoi="10.5281/zenodo.4691101")
    assert rec2.version != 'v1.1', "There ought to be a newer version for this conceptdoi!"


@pytest.mark.integration
def test_versions(API):  # pragma: no cover
    assert len(list(API.iter_versions('10.5281/zenodo.3260727'))) > 5


@pytest.mark.integration
def test_download(API, tmp_path):  # pragma: no cover
    rec = API.get_record(doi="10.5281/zenodo.3603755")
    assert rec.download_urls, str(rec.download_urls)
    rec.download(tmp_path, unwrap=False, prefer_github=False)
    assert tmp_path.joinpath('cldf-datasets-petersonsouthasia-e029fbf').exists(), \
        [n.name for n in tmp_path.iterdir()]
    ds = rec.download_dataset(tmp_path)
    assert len(ds.objects('LanguageTable')) == 29
