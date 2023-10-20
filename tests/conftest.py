import pathlib

import pytest


@pytest.fixture
def fixtures_dir():
    return pathlib.Path(__file__).parent / 'fixtures'


@pytest.fixture
def urlopen(fixtures_dir):
    class Response:
        def __init__(self, fname):
            self.path = fixtures_dir / fname

        def read(self):
            return self.path.read_bytes()

    def f(req):
        if '/communities?' in req.full_url:
            return Response('communities.json')
        elif 'doi%3A' in req.full_url:
            return Response('record.json')
        return Response('search_keyword.json')

    return f
