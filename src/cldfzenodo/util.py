import urllib.parse
import urllib.request


class RecordGenerator:
    __base_url__ = None

    def __init__(self, text):
        self.text = text

    @classmethod
    def from_params(cls, **params):
        comps = urllib.parse.urlparse(cls.__base_url__)
        url = urllib.parse.urlunparse(list(comps[:3]) + ['', urllib.parse.urlencode(params), ''])
        return cls.from_url(url)

    @classmethod
    def from_url(cls, url):
        return cls(urllib.request.urlopen(url).read().decode('utf8'))

    def iter_records(self):
        raise NotImplementedError()  # pragma: no cover

    def __iter__(self):
        yield from self.iter_records()
        next = self.next()
        while next:
            yield from next.iter_records()
            next = next.next()

    def next(self):
        raise NotImplementedError()  # pragma: no cover
