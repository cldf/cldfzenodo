"""
curl -H "accept: application/json" "https://zenodo.org/api/records/?keywords=cldf:Wordlist"
"""
import json
import urllib.parse
import urllib.request

from cldfzenodo.record import Record, GithubRepos, ZENODO_DOI_FORMAT

__all__ = ['iter_records']


class Results:
    __base_url__ = "https://zenodo.org/api/records/"

    def __init__(self, text):
        self.json = json.loads(text)

    @classmethod
    def from_params(cls, **params):
        comps = urllib.parse.urlparse(cls.__base_url__)
        url = urllib.parse.urlunparse(list(comps[:3]) + ['', urllib.parse.urlencode(params), ''])
        return cls.from_url(url)

    @classmethod
    def from_url(cls, url):
        return cls(urllib.request.urlopen(url).read().decode('utf8'))

    def __iter__(self):
        yield from self.iter_records()
        next = self.next()
        while next:
            yield from next.iter_records()
            next = next.next()

    @staticmethod
    def record(d):
        for v in d['metadata']['relations']['version']:
            if 'parent' in v and v['parent']['pid_type'] == 'recid':
                conceptrecid = v['parent']['pid_value']
                break
        else:
            raise ValueError('Missing concept recid!')  # pragma: no cover
        kw = dict(
            doi=d['doi'],
            title=d['metadata']['title'],
            keywords=d['metadata'].get('keywords'),
            communities=[
                dd.get('identifier', dd.get('id')) for dd in d['metadata'].get('communities', [])],
            closed_access=d['metadata']['access_right'] == 'closed',
            creators=[c['name'] for c in d['metadata']['creators']],
            year=d['metadata']['publication_date'].split('-')[0],
            license=d['metadata'].get('license', {}).get('id'),
            version=d['metadata'].get('version'),
            concept_doi=ZENODO_DOI_FORMAT.format(conceptrecid),
        )
        if d.get('files'):
            kw['download_urls'] = [d['files'][0]['links']['self']]
        for ri in d['metadata']['related_identifiers']:
            if ri['relation'] == 'isSupplementTo':
                kw['github_repos'] = GithubRepos.from_url(ri['identifier'])
        return Record(**kw)

    def iter_records(self):
        for rec in self.json['hits']['hits']:
            yield self.record(rec)

    def next(self):
        if self.json['links'].get('next'):
            return Results.from_url(self.json['links']['next'])


def iter_records(keyword, q=None, **kw):
    params = dict(keywords=keyword)
    if q:
        params['q'] = q  # pragma: no cover
    params.update(kw)
    for rec in Results.from_params(**params):
        yield rec
