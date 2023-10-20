import warnings

from clldutils.misc import deprecated

from cldfzenodo.record import *
from cldfzenodo.api import *
from cldfzenodo import oai
from cldfzenodo import search

__version__ = '2.0.1.dev0'
# flake8: noqa

# -------------------------------------------------------------------------------------------------
# legacy API:
# -------------------------------------------------------------------------------------------------
def search_wordlists(q=None, **kw):
    deprecated('Use `API.iter_records` instead.')
    if kw:
        warnings.warn('Zenodo search API changed, custom parameters passed as kw are ignored.')
    return API.iter_records(keyword='cldf:Wordlist', allversions=True, _q=q)


def search_structuredatasets(q=None, **kw):
    deprecated('Use `API.iter_records` instead.')
    if kw:
        warnings.warn('Zenodo search API changed, custom parameters passed as kw are ignored.')
    return API.iter_records(keyword='cldf:StructureDataset', allversions=True, _q=q)


def oai_lexibank():
    deprecated('Use `API.iter_records` instead.')
    return API.iter_records(community='lexibank', allversions=True)


def oai_cldf_datasets():
    deprecated('Use `API.iter_records` instead.')
    return API.iter_records(community='cldf-datasets', allversions=True)
