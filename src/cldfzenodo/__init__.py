import functools

from cldfzenodo.record import Record
from cldfzenodo import oai
from cldfzenodo import search

__version__ = '0.2.1.dev0'

assert Record
search_wordlists = functools.partial(search.iter_records, 'cldf:Wordlist')
search_structuredatasets = functools.partial(search.iter_records, 'cldf:StructureDataset')
oai_lexibank = functools.partial(oai.iter_records, 'lexibank')
oai_cldf_datasets = functools.partial(oai.iter_records, 'cldf-datasets')
