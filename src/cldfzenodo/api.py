import re
import json
import shlex
import typing
import subprocess
import urllib.error
import urllib.parse
import urllib.request

from pycldf import Source
from pycldf.ext.discovery import DatasetResolver
from clldutils.path import ensure_cmd

from cldfzenodo.record import Record, ZENODO_DOI_FORMAT, ZENODO_DOI_PATTERN, get_doi

__all__ = ['API', 'Api', 'ZenodoResolver']


def get_hits(res: typing.Union[str, dict, list]) -> typing.List[dict]:
    if isinstance(res, str):
        res = json.loads(res)
    return res if isinstance(res, list) else res['hits']['hits']


def q(**kw) -> str:
    """
    Put together a Zenodo search query from the data in `kw`.

    See https://help.zenodo.org/guides/search/ for details.
    """
    res = kw.pop('_q', '') or ''
    if kw:
        res += '' + ' '.join('{}:"{}"'.format(k, v) for k, v in kw.items())
    return res.strip()


class Results:
    def __init__(self,
                 api: 'Api',
                 allversions: typing.Optional[bool] = False,
                 community: typing.Optional[str] = None,
                 **params: str):
        """
        :param params: URL parameters (see https://developers.zenodo.org/#records)
        """
        self.api = api
        self.params = params
        self.community = community
        if allversions:
            self.params['allversions'] = 'true'
        self._page = 0
        self.more = True
        self.error = None

    def next(self) -> typing.List[Record]:
        self._page += 1
        params = {
            'sort': '-mostrecent',
            'page': str(self._page),
            'size': str(self.api.page_size)}
        params.update(self.params)
        try:
            hits = get_hits(self.api.records(community=self.community, params=params))
        except urllib.error.HTTPError as e:  # pragma: no cover
            # We want to be able to resume retrieval of results.
            hits = []
            self.error = e
            self._page -= 1
            raise
        self.more = len(hits) >= self.api.page_size
        return [Record.from_dict(r) for r in hits]


class Api:
    __base_url__ = "https://zenodo.org/api/"
    __communities__ = {}  # We cash community identifiers.

    def __init__(self, page_size=100):
        self.page_size = page_size

    def __call__(self,
                 what: str,
                 id_: typing.Optional[str] = None,
                 params: typing.Optional[typing.Dict[str, str]] = None,
                 headers: typing.Optional[typing.Dict[str, str]] = None,
                 _verbose: bool = False) -> str:
        """
        Perform an API call and return the response body as str.

        :param what: Name of the API resource, e.g. "records".
        :param id_: Optional identifier of a resource instance.
        :param params: URL query parameters.
        :param headers: HTTP request headers.
        :param _verbose:
        :return: Body of the response as text.
        """
        params = params or {}
        headers = headers or {}
        comps = urllib.parse.urlparse(
            self.__base_url__ + '{}{}'.format(what, '/' + id_ if id_ else ''))
        url = urllib.parse.urlunparse(list(comps[:3]) + ['', urllib.parse.urlencode(params), ''])
        req = urllib.request.Request(url)
        for k, v in headers.items():
            req.add_header(k, v)
        if _verbose:  # pragma: no cover
            print(url)
        return urllib.request.urlopen(req).read().decode('utf8')

    def records(self,
                id_: typing.Optional[str] = None,
                community: typing.Optional[str] = None,
                params: typing.Optional[typing.Dict[str, str]] = None,
                headers: typing.Optional[typing.Dict[str, str]] = None) -> str:
        """
        Perfom an API call to the records resource (possibly limited to one community).

        :param id_: Optional record identifier.
        :param community: Zenodo community identifier. If specified, only records in this community\
        are considered.
        :param params: URL query parameters.
        :param headers: HTTP request headers.
        :return: Body of the response as text.
        """
        what = ''
        if community:
            if community not in self.__communities__:
                res = get_hits(self('communities', params=dict(q=community)))
                self.__communities__[community] = res[0]['id']
            what = 'communities/{}/'.format(self.__communities__[community])
        what += 'records'
        return self(what, id_=id_, params=params, headers=headers)

    def iter_versions(self, conceptdoi: str) -> typing.Generator[Record, None, None]:
        """
        Retrieve all versions recorded for a concept DOI.
        """
        yield from self.iter_records(conceptdoi=get_doi(conceptdoi), allversions=True)

    @staticmethod
    def _first_record(res):
        hits = get_hits(res)
        if hits:
            return Record.from_dict(hits[0])

    def get_record(self,
                   doi: typing.Optional[str] = None,
                   conceptdoi: typing.Optional[str] = None,
                   version: typing.Optional[str] = None) -> typing.Union[Record, None]:
        """
        Retrieve a record specified by Zenodo DOI, given as URL or plain.

        :param doi: A Zenodo DOI or URL identifying a record (i.e. no concept DOI).
        :param conceptdoi: A Zenodo concept DOI. If no `version` is passed, the latest matching \
        record will be returned.
        :param version: A version tag, used to choose a particular record when only a concept doi \
        is passed.
        :return: A `Record` instance, if one is found, else `None`.
        """
        if doi:
            doi = get_doi(doi)
            assert not conceptdoi
            return self._first_record(self.records(params=dict(allversions='true', q=q(doi=doi))))
        assert conceptdoi
        conceptdoi = get_doi(conceptdoi)
        if not version:
            return self._first_record(self.records(params=dict(q=q(conceptdoi=conceptdoi))))
        for rec in self.iter_records(conceptdoi=conceptdoi, allversions=True):
            if rec.version.lstrip('v') == version.lstrip('v'):
                return rec

    def iter_records(self,
                     community: typing.Optional[str] = None,
                     keyword: typing.Optional[str] = None,
                     allversions: typing.Optional[bool] = False,
                     **kw
                     ) -> typing.Generator[Record, None, Results]:
        """
        Retrieve records matching various search criteria.

        :param community: A Zenodo community identifier.
        :param keyword: A keyword associated with relevant records.
        :param allversions: A flag signaling whether only the latest version of each record is \
        retrieved (the default) or all.
        :param kw: Additional search terms according to the Zenodo search query language.
        :return: A generator of records.
        """
        if keyword:
            kw['keywords'] = keyword
        res = Results(self, allversions=allversions, community=community, q=q(**kw))
        yield from res.next()
        while res.more:
            yield from res.next()  # pragma: no cover
        if res.error:
            return res  # pragma: no cover

    def get_github_release_info(
            self,
            repos: str,
            tag: typing.Optional[str] = None,
            bibid: typing.Optional[str] = None
    ) -> typing.Tuple[
        typing.Union[str, None],
        typing.Union[str, None],
        typing.Union[str, None],
        typing.Union[Source, None]
    ]:
        """
        Get information about a GitHub repository release that has been archived with Zenodo.

        We assume, that the DOI of the upload on Zenodo has been added to the release description
        on GitHub.

        :param repos: GitHub repository specifier in the form `org/repo`.
        :param tag: Optional version tag.
        :param bibid: Optional identifier to use for the BibTeX record.
        :return: A quadruple (tag, DOI, APA citation, BibTeX record)
        """
        def gh(args):
            return subprocess.check_output([ensure_cmd('gh')] + shlex.split(args)).decode('utf8')

        version_pattern = re.compile(r'(?P<tag>v[0-9]+\.[0-9]+(\.[0-9]+)?)')
        doi_pattern = re.compile(r'https://doi\.org/(?P<doi>10\.5281/zenodo\.[0-9]+)')

        if not tag:
            latest = gh('release list -L 1 -R {}'.format(repos))
            if not latest:
                return None, None, None, None  # pragma: no cover
            match = version_pattern.search(latest)
            assert match, latest
            tag = match.group('tag')

        info = gh('release view {} -R {}'.format(tag, repos))
        match = None
        for match in doi_pattern.finditer(info):
            pass
        if match:
            doi = match.group('doi')
            if doi:
                cit = self.records(
                    id_=ZENODO_DOI_PATTERN.match(doi).group('recid'),
                    params=dict(style='apa'),
                    headers=dict(Accept='text/x-bibliography')).strip()
                bib = self.records(
                    id_=ZENODO_DOI_PATTERN.match(doi).group('recid'),
                    params=dict(style='bibtex'),
                    headers=dict(Accept='text/x-bibliography')).strip()
                bib = Source.from_bibtex(re.sub(
                    r', (?P<field>[a-zA-Z]+)=',
                    lambda m: ',\n  {} = '.format(m.group('field')),
                    bib), _check_id=False)
                bib.id = bibid or repos.replace('/', '_')
                for field in ['abstractNote', 'month']:
                    if field in bib:
                        del bib[field]
                bib['edition'] = tag
                bib['type'] = 'Data set'
                return tag, doi, cit, bib
        return tag, None, None, None  # pragma: no cover


# Since an Api instance does some caching, we provide one instance as module global.
API = Api()


class ZenodoResolver(DatasetResolver):
    def __call__(self, loc, download_dir):
        doi = None
        m = ZENODO_DOI_PATTERN.search(loc)
        if m:
            doi = loc[m.start():m.end()]
        else:
            m = re.search(r'zenodo\.org/record(s)?/(?P<number>[0-9]+)', loc)
            if m:
                doi = ZENODO_DOI_FORMAT.format(m.group('number'))
        if doi:
            rec = API.get_record(doi=doi) or API.get_record(conceptdoi=doi)
            return rec.download(download_dir)
