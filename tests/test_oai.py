from cldfzenodo.oai import iter_records


def test_iter_records(mocker, tests_dir):
    def urlopen(url):
        xml = tests_dir.joinpath('oai.xml').read_text(encoding='utf8')
        if 'resumptionToken' in url:
            xml = '\n'.join(line for line in xml.split('\n') if 'resumptionToken' not in line)
        return mocker.Mock(read=lambda: xml.encode('utf8'))

    mocker.patch('cldfzenodo.record.urllib.request.urlopen', urlopen)
    assert len(list(iter_records('x'))) == 200
