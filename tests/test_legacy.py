
def test_legacy(urlopen, mocker, recwarn):
    from cldfzenodo import (
        search_wordlists, search_structuredatasets, oai_cldf_datasets, oai_lexibank,
    )
    from cldfzenodo.oai import iter_records
    from cldfzenodo import search

    mocker.patch('cldfzenodo.api.urllib.request.urlopen', urlopen)

    res = list(search_wordlists(sort='x'))
    assert len(res) == 10
    assert recwarn.pop(UserWarning)
    assert recwarn.pop(DeprecationWarning)

    res = list(search_structuredatasets(sort='x'))
    assert len(res) == 10
    assert recwarn.pop(UserWarning)
    assert recwarn.pop(DeprecationWarning)

    res = list(oai_lexibank())
    assert len(res) == 10
    assert recwarn.pop(DeprecationWarning)

    res = list(oai_cldf_datasets())
    assert len(res) == 10
    assert recwarn.pop(DeprecationWarning)

    res = list(iter_records('x'))
    assert len(res) == 10
    assert recwarn.pop(DeprecationWarning)

    res = list(search.iter_records(None, q='x'))
    assert len(res) == 10
    assert recwarn.pop(DeprecationWarning)
