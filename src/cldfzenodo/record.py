"""
Zenodo deposit record, as described by the DCAT metadata.
"""
import io
import re
import shutil
import typing
import pathlib
import zipfile
import tempfile
import urllib.parse
import urllib.request

import attr
import nameparser
from pycldf import iter_datasets, Source, Dataset

__all__ = ['Record', 'GithubRepos', 'ZENODO_DOI_FORMAT', 'ZENODO_DOI_PATTERN', 'get_doi']

ZENODO_DOI_PATTERN = re.compile(r"10\.5281/zenodo\.(?P<recid>[0-9]+)")
DOI_PATTERN = re.compile(r"10\.[0-9.]+/[^/]+")
ZENODO_DOI_FORMAT = '10.5281/zenodo.{}'
NS = dict(
    rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    adms="http://www.w3.org/ns/adms#",
    dc="http://purl.org/dc/elements/1.1/",
    dct="http://purl.org/dc/terms/",
    citedcat="https://w3id.org/citedcat-ap/",
    dctype="http://purl.org/dc/dcmitype/",
    dcat="http://www.w3.org/ns/dcat#",
    duv="http://www.w3.org/ns/duv#",
    foaf="http://xmlns.com/foaf/0.1/",
    frapo="http://purl.org/cerif/frapo/",
    geo="http://www.w3.org/2003/01/geo/wgs84_pos#",
    gsp="http://www.opengis.net/ont/geosparql#",
    locn="http://www.w3.org/ns/locn#",
    org="http://www.w3.org/ns/org#",
    owl="http://www.w3.org/2002/07/owl#",
    prov="http://www.w3.org/ns/prov#",
    rdfs="http://www.w3.org/2000/01/rdf-schema#",
    schema="http://schema.org/",
    skos="http://www.w3.org/2004/02/skos/core#",
    vcard="http://www.w3.org/2006/vcard/ns#",
    wdrs="http://www.w3.org/2007/05/powder-s#",
)


@attr.s
class GithubRepos:
    """
    Zenodo deposits via the GitHub-Zenodo bridge carry enough metadata to retrieve the source
    repository. This info is particularly interesting for us, because we prefer downloading
    releases from GitHub over Zenodo, due to Zenodo's rate-limiting.

    :ivar str org: GitHub organization name of the repository
    :ivar str name: repository name
    :ivar str tag: release tag of the version of the repository that was deposited on Zenodo
    """
    org = attr.ib()
    name = attr.ib()
    tag = attr.ib(default=None)

    @classmethod
    def from_url(cls, url: str) -> 'GithubRepos':
        url = urllib.parse.urlparse(url)
        if url.netloc == 'github.com':
            path = url.path.split('/')
            return cls(
                org=path[1],
                name=path[2],
                tag=path[4] if len(path) > 4 and path[3] == 'tree' else None)

    @property
    def clone_url(self) -> str:
        """
        :return: A URL suitable for passing to `git clone`.
        """
        return 'https://github.com/{0.org}/{0.name}.git'.format(self)

    @property
    def release_url(self) -> typing.Union[None, str]:
        """
        :return: The URL of a zipped release on GitHub.
        """
        if self.tag:
            return 'https://github.com/{0.org}/{0.name}/archive/refs/tags/{0.tag}.zip'.format(self)


def get_doi(doi_or_url: str) -> str:
    """

    .. code-block:: python

        >>> get_doi('10.5281/zenodo.5173799')
        '10.5281/zenodo.5173799'
        >>> get_doi("https://doi.org/10.5281/zenodo.5173799")
        '10.5281/zenodo.5173799'
        >>> get_doi("https://zenodo.org/doi/10.5281/zenodo.5173799")
        '10.5281/zenodo.5173799'
        >>> get_doi("https://zenodo.org/record/5173799")
        '10.5281/zenodo.5173799'
        >>> get_doi("https://zenodo.org/records/5173799")
        '10.5281/zenodo.5173799'
    """
    url, doi = urllib.parse.urlparse(doi_or_url), None
    if not url.netloc:
        doi = url.path
    elif url.netloc == 'zenodo.org':
        if url.path.startswith('/doi/'):
            doi = url.path.replace('/doi/', '')
        else:
            doi = ZENODO_DOI_FORMAT.format(url.path.split('/')[-1])
    elif url.netloc == 'doi.org':
        doi = url.path[1:]
    else:
        raise ValueError('Unknown DOI format')
    if not (ZENODO_DOI_PATTERN.fullmatch(doi) or DOI_PATTERN.fullmatch(doi)):
        raise ValueError('Not a DOI: "{}"'.format(doi))
    return doi


def get_creators(names):
    res = []
    for name in names:
        name = nameparser.HumanName(name)
        first = name.first
        if name.middle:
            first += ' ' + name.middle
        res.append('{}, {}'.format(name.last, first))
    return res


@attr.s
class Record:
    """
    Metadata of a Zenodo deposit

    :ivar doi: The DOI of the record.
    :ivar title: The title of the record.
    :ivar typing.List[str] creators: List of names of the creators of the record.
    """
    doi = attr.ib(
        converter=get_doi,
        validator=attr.validators.matches_re(DOI_PATTERN))
    title = attr.ib()
    creators = attr.ib(converter=get_creators, default=attr.Factory(list))
    year = attr.ib(default=None)
    license = attr.ib(default=None)
    download_urls = attr.ib(default=attr.Factory(list))
    keywords = attr.ib(default=attr.Factory(list))
    communities = attr.ib(default=attr.Factory(list), converter=lambda c: [i for i in c if i])
    github_repos = attr.ib(default=None)
    closed_access = attr.ib(default=False, validator=attr.validators.instance_of(bool))
    version = attr.ib(default=None)
    concept_doi = attr.ib(default=None)
    metadata = attr.ib(default=attr.Factory(dict))

    def __attrs_post_init__(self):
        if not self.download_url:
            assert self.closed_access, self.doi

    @property
    def download_url(self) -> typing.Union[str, None]:
        return self.download_urls[0] if self.download_urls else None

    @property
    def id(self) -> str:
        """
        :return: The Zenodo recid.
        """
        return self.doi.replace('10.5281/zenodo.', '')

    @property
    def version_tag(self) -> typing.Union[None, str]:  # pragma: no cover
        return self.version or (self.github_repos.tag if self.github_repos else None)

    @classmethod
    def from_dict(cls, d):
        kw = dict(
            doi=d['doi'],
            title=d['metadata']['title'],
            keywords=d['metadata'].get('keywords'),
            communities=[
                dd.get('identifier', dd.get('id')) for dd in d['metadata'].get('communities', [])],
            closed_access=d['metadata']['access_right'] in {'closed', 'restricted'},
            creators=[c['name'] for c in d['metadata']['creators']],
            year=d['metadata']['publication_date'].split('-')[0],
            version=d['metadata'].get('version'),
            concept_doi=d.get('conceptdoi'),  # There are old records with "concept_rec_id" ...
            # FIXME: Check Zenodo API periodically to see whether URLs are correct now.
            download_urls=[f['links']['self'].replace('/api/', '/') for f in d.get('files')],
            metadata=d['metadata']
        )
        if 'license' in d['metadata']:
            lic = d['metadata']['license']
            kw['license'] = lic if isinstance(lic, str) else lic.get('identifier', lic.get('id'))
        for ri in d['metadata'].get('related_identifiers', []):
            if ri['relation'] == 'isSupplementTo':
                kw['github_repos'] = GithubRepos.from_url(ri['identifier'])
        return cls(**kw)

    @staticmethod
    def _download(url, dest, log=None):
        urlpath = pathlib.Path(urllib.parse.urlparse(url).path)
        with urllib.request.urlopen(url) as res:
            if res.code == 200:
                if log:
                    log.info('Downloading {}'.format(url))
                if urlpath.suffix == '.zip':
                    zipfile.ZipFile(io.BytesIO(res.read())).extractall(path=dest)
                else:
                    dest.joinpath(urlpath.name).write_bytes(res.read())

    def download(self, dest, log=None, unwrap=True, prefer_github=True) -> pathlib.Path:
        """
        Download the zipped file-content of the record to `dest`.

        :param dest:
        :param log:
        :return: The directory containing the unzipped files of the record.
        """
        dest = pathlib.Path(dest)
        is_empty = not dest.exists() or (len(list(dest.iterdir())) == 0)
        if not dest.exists():
            dest.mkdir()
        if not self.download_urls:
            raise ValueError('No downloadable resources')  # pragma: no cover
        # Preferentially download from github to not run into Zenodo's rate limit.
        if prefer_github and self.github_repos and self.github_repos.release_url:
            self._download(self.github_repos.release_url, dest, log=log)
        else:
            for url in self.download_urls:
                if url.endswith('/content'):
                    url = url[:-len('/content')]  # pragma: no cover
                self._download(url, dest, log=log)
        inner = list(dest.iterdir())
        if unwrap and is_empty and len(inner) == 1 and inner[0].is_dir():
            # Move the content of the inner-directory to dest:
            for p in inner[0].iterdir():
                shutil.move(str(p), str(dest))
            inner[0].rmdir()
        return dest

    def download_dataset(self, dest, condition=None, mdname=None, log=None) -> Dataset:
        with tempfile.TemporaryDirectory() as tmpdirname:
            for ds in iter_datasets(self.download(tmpdirname, log=log)):
                if (condition is None) or condition(ds):
                    return Dataset.from_metadata(ds.copy(dest, mdname=mdname))

    def get_bibtex(self, bibid=None) -> str:
        src = Source(
            'misc',
            bibid or self.doi.split('/')[-1].replace('.', '-'),
            author=' and '.join(self.creators),
            title=self.title,
            keywords=', '.join(self.keywords),
            publisher='Zenodo',
            year=self.year,
            edition=self.version,
            doi=self.doi,
            type='Data set',
            url='https://doi.org/{}'.format(self.doi),
        )
        if self.license:
            src['copyright'] = self.license
        return src.bibtex()

    @property
    def bibtex(self) -> str:
        return self.get_bibtex()

    def get_citation(self, api) -> str:
        # curl -H "Accept:text/x-bibliography" "https://zenodo.org/api/records/7079637?style=apa
        return api.records(
            id_=self.id,
            params=dict(style='apa'),
            headers=dict(Accept='text/x-bibliography')).strip()

    # ---------------------------------------------------------------------------------------------
    # legacy API:
    # ---------------------------------------------------------------------------------------------
    @staticmethod
    def from_doi(doi):  # pragma: no cover
        from cldfzenodo import API
        return API.get_record(doi=doi)

    @staticmethod
    def from_concept_doi(doi, version_tag=None):  # pragma: no cover
        from cldfzenodo import API
        return API.get_record(conceptdoi=doi, version=version_tag)

    @property
    def citation(self):  # pragma: no cover
        from cldfzenodo import API
        return self.get_citation(API)
