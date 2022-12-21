from clldutils.oaipmh import Response, qname, Record

from cldfzenodo.oai import iter_records


def test_iter_records(mocker, tests_dir):
    def _recs():
        res = Response(tests_dir.joinpath('oai.xml').read_text(encoding='utf8'))
        for e in res.xml.findall('.//{}'.format(qname('record'))):
            yield Record.from_element(e)

    mocker.patch('cldfzenodo.oai.oaipmh', mocker.Mock(iter_records=lambda *args, **kw: _recs()))
    assert len(list(iter_records('x'))) == 100
