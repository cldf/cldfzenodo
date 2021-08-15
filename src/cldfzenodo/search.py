"""
curl -H "accept: application/json" "https://zenodo.org/api/records/?keywords=cldf:Wordlist"
"""
import json

from cldfzenodo.record import Record, GithubRepos
from cldfzenodo.util import RecordGenerator


class Results(RecordGenerator):
    __base_url__ = "https://zenodo.org/api/records/"

    def __init__(self, text):
        RecordGenerator.__init__(self, text)
        self.json = json.loads(self.text)

    @staticmethod
    def record(d):
        kw = dict(
            doi=d['doi'],
            title=d['metadata']['title'],
            keywords=d['metadata']['keywords'],
            communities=[dd.get('identifier', dd.get('id')) for dd in d['metadata']['communities']],
            closed_access=d['metadata']['access_right'] == 'closed',
        )
        if d.get('files'):
            kw['download_url'] = d['files'][0]['links']['self']
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
