import json

from cldfzenodo.search import iter_records


def test_iter_records(mocker, tests_dir):
    def urlopen(url):
        content = json.loads(tests_dir.joinpath('search.json').read_text(encoding='utf8'))
        if 'page=2' in url:
            del content['links']['next']
        return mocker.Mock(read=lambda: json.dumps(content).encode('utf8'))

    mocker.patch('cldfzenodo.record.urllib.request.urlopen', urlopen)
    assert len(list(iter_records('x'))) == 2
