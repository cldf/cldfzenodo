"""
Zenodo deposit record, as described by the DCAT metadata.
"""

import io
import logging
import re
import shutil
from typing import Optional, Union, Any, Callable, TYPE_CHECKING
import pathlib
import zipfile
import tempfile
import dataclasses
import urllib.parse
import urllib.request

import nameparser
from pycldf import iter_datasets, Source, Dataset

if TYPE_CHECKING:
    from cldfzenodo import Api  # pragma: no cover

__all__ = [
    "Record",
    "GithubRepos",
    "ZENODO_DOI_FORMAT",
    "ZENODO_DOI_PATTERN",
    "get_doi",
]

ZENODO_DOI_PATTERN = re.compile(r"10\.5281/zenodo\.(?P<recid>[0-9]+)")
DOI_PATTERN = re.compile(r"10\.[0-9.]+/[^/]+")
ZENODO_DOI_FORMAT = "10.5281/zenodo.{}"
NS = dict(  # pylint: disable=R1735
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


@dataclasses.dataclass
class GithubRepos:
    """
    Zenodo deposits via the GitHub-Zenodo bridge carry enough metadata to retrieve the source
    repository. This info is particularly interesting for us, because we prefer downloading
    releases from GitHub over Zenodo, due to Zenodo's rate-limiting.

    :ivar str org: GitHub organization name of the repository
    :ivar str name: repository name
    :ivar str tag: release tag of the version of the repository that was deposited on Zenodo
    """

    org: str
    name: str
    tag: str = None

    @classmethod
    def from_url(cls, url: str) -> Optional["GithubRepos"]:
        """Instantiate a GithubRepos from a GitHub URL."""
        url = urllib.parse.urlparse(url)
        if url.netloc == "github.com":
            path = url.path.split("/")
            return cls(
                org=path[1],
                name=path[2],
                tag=path[4] if len(path) > 4 and path[3] == "tree" else None,
            )
        return None

    @property
    def clone_url(self) -> str:
        """
        :return: A URL suitable for passing to `git clone`.
        """
        return f"https://github.com/{self.org}/{self.name}.git"

    @property
    def release_url(self) -> Optional[str]:
        """
        :return: The URL of a zipped release on GitHub.
        """
        if self.tag:
            return f"https://github.com/{self.org}/{self.name}/archive/refs/tags/{self.tag}.zip"
        return None  # pragma: no cover


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
    elif url.netloc == "zenodo.org":
        if url.path.startswith("/doi/"):
            doi = url.path.replace("/doi/", "")
        else:
            doi = ZENODO_DOI_FORMAT.format(url.path.split("/")[-1])
    elif url.netloc == "doi.org":
        doi = url.path[1:]
    else:
        raise ValueError("Unknown DOI format")
    if not (ZENODO_DOI_PATTERN.fullmatch(doi) or DOI_PATTERN.fullmatch(doi)):
        raise ValueError(f'Not a DOI: "{doi}"')
    return doi


@dataclasses.dataclass
class Record:  # pylint: disable=too-many-instance-attributes
    """
    Metadata of a Zenodo deposit

    :ivar doi: The DOI of the record.
    :ivar title: The title of the record.
    :ivar typing.List[str] creators: List of names of the creators of the record.
    """

    doi: str
    title: str
    creators: list[str] = dataclasses.field(default_factory=list)
    year: Optional[str] = None
    license: Optional[str] = None
    download_urls: list[str] = dataclasses.field(default_factory=list)
    keywords: list[str] = dataclasses.field(default_factory=list)
    communities: list[str] = dataclasses.field(default_factory=list)
    github_repos: Optional[str] = None
    closed_access: bool = False
    version: Optional[str] = None
    concept_doi: Optional[str] = None
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        self.doi = get_doi(self.doi)
        assert DOI_PATTERN.match(self.doi)

        formatted = []
        for name in self.creators:
            name = nameparser.HumanName(name)
            first = name.first
            if name.middle:
                first += " " + name.middle
            formatted.append(f"{name.last}, {first}")
        self.creators = formatted

        self.communities = [i for i in self.communities if i]
        assert isinstance(self.closed_access, bool)
        if not self.download_url:
            assert self.closed_access, self.doi

    @property
    def download_url(self) -> Optional[str]:
        """The first download URL specified for the record."""
        return self.download_urls[0] if self.download_urls else None

    @property
    def id(self) -> str:
        """
        :return: The Zenodo recid.
        """
        return self.doi.replace("10.5281/zenodo.", "")

    @property
    def version_tag(self) -> Optional[str]:  # pragma: no cover
        """The closest thing to a version tag, found for the record."""
        return self.version or (self.github_repos.tag if self.github_repos else None)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Record":
        """Instantiate a record from the JSON metadata delivered by the Zenodo API."""
        kw = dict(  # pylint: disable=R1735
            doi=d["doi"],
            title=d["metadata"]["title"],
            keywords=d["metadata"].get("keywords"),
            communities=[
                dd.get("identifier", dd.get("id"))
                for dd in d["metadata"].get("communities", [])
            ],
            closed_access=d["metadata"]["access_right"] in {"closed", "restricted"},
            creators=[c["name"] for c in d["metadata"]["creators"]],
            year=d["metadata"]["publication_date"].split("-")[0],
            version=d["metadata"].get("version"),
            concept_doi=d.get(
                "conceptdoi"
            ),  # There are old records with "concept_rec_id" ...
            # FIXME:  # pylint: disable=fixme
            # Check Zenodo API periodically to see whether URLs are correct now.
            download_urls=[
                f["links"]["self"].replace("/api/", "/") for f in d.get("files")
            ],
            metadata=d["metadata"],
        )
        if "license" in d["metadata"]:
            lic = d["metadata"]["license"]
            kw["license"] = lic if isinstance(lic, str) else lic.get("identifier", lic.get("id"))
        for ri in d["metadata"].get("related_identifiers", []):
            if ri["relation"] == "isSupplementTo":
                kw["github_repos"] = GithubRepos.from_url(ri["identifier"])
        return cls(**kw)

    @staticmethod
    def _download(url, dest, log=None):
        urlpath = pathlib.Path(urllib.parse.urlparse(url).path)
        with urllib.request.urlopen(url) as res:
            if res.code == 200:
                if log:
                    log.info("Downloading %s", url)
                if urlpath.suffix == ".zip":
                    with zipfile.ZipFile(io.BytesIO(res.read())) as zipf:
                        zipf.extractall(path=dest)
                else:
                    dest.joinpath(urlpath.name).write_bytes(res.read())

    def download(
            self,
            dest: Union[str, pathlib.Path],
            log: Optional[logging.Logger] = None,
            unwrap: bool = True,
            prefer_github: bool = True,
    ) -> pathlib.Path:
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
            raise ValueError("No downloadable resources")  # pragma: no cover
        # Preferentially download from github to not run into Zenodo's rate limit.
        if prefer_github and self.github_repos and self.github_repos.release_url:
            self._download(self.github_repos.release_url, dest, log=log)
        else:
            for url in self.download_urls:
                if url.endswith("/content"):
                    url = url[: -len("/content")]  # pragma: no cover
                self._download(url, dest, log=log)
        inner = list(dest.iterdir())
        if unwrap and is_empty and len(inner) == 1 and inner[0].is_dir():
            # Move the content of the inner-directory to dest:
            for p in inner[0].iterdir():
                shutil.move(str(p), str(dest))
            inner[0].rmdir()
        return dest

    def download_dataset(
            self,
            dest: Union[str, pathlib.Path],
            condition: Optional[Callable[[Dataset], bool]] = None,
            mdname: Optional[str] = None,
            log: Optional[logging.Logger] = None,
    ) -> Optional[Dataset]:
        """Download a particular CLDF dataset contained in the Zenodo deposit."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            for ds in iter_datasets(self.download(tmpdirname, log=log)):
                if (condition is None) or condition(ds):
                    return Dataset.from_metadata(ds.copy(dest, mdname=mdname))
        return None  # pragma: no cover

    def get_bibtex(self, bibid: Optional[str] = None) -> str:
        """Compose a BibTeX item from the metadata of the record."""
        src = Source(
            "misc",
            bibid or self.doi.split("/")[-1].replace(".", "-"),
            author=" and ".join(self.creators),
            title=self.title,
            keywords=", ".join(self.keywords),
            publisher="Zenodo",
            year=self.year,
            edition=self.version,
            doi=self.doi,
            type="Data set",
            url=f"https://doi.org/{self.doi}",
        )
        if self.license:
            src["copyright"] = self.license
        return src.bibtex()

    @property
    def bibtex(self) -> str:
        """BibTeX-formatted metadata for the record."""
        return self.get_bibtex()

    def get_citation(self, api: 'Api') -> str:
        """
        Get a formatted citation for the record.

        curl -H "Accept:text/x-bibliography" "https://zenodo.org/api/records/7079637?style=apa
        """
        return api.records(
            id_=self.id, params={'style': "apa"}, headers={'Accept': "text/x-bibliography"}).strip()
