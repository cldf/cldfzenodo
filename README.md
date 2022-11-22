# cldfzenodo

[![Build Status](https://github.com/cldf/cldfzenodo/workflows/tests/badge.svg)](https://github.com/cldf/cldfzenodo/actions?query=workflow%3Atests)
[![PyPI](https://img.shields.io/pypi/v/cldfzenodo.svg)](https://pypi.org/project/cldfzenodo)

`cldfzenodo` provides programmatic access to CLDF data deposited on [Zenodo](https://zenodo.org).


## Install

```shell
pip install cldfzenodo
```


## `pycldf` dataset resolver

`cldfzenodo` registers (upon installation) a [`pycldf` dataset resolver](https://pycldf.readthedocs.io/en/latest/ext_discovery.html)
for dataset locators of the form `https://doi.org/10.5281/zenodo.[0-9]+` and `https://zenodo.org/record/[0-9]+`.
Thus, after installation you should be able to retrieve `pycldf.Dataset` instances running

```python
>>> from pycldf.ext.discovery import get_dataset
>>> import pathlib
>>> pathlib.Path('wacl').mkdir()
>>> ds = get_dataset('https://doi.org/10.5281/zenodo.7322688', pathlib.Path('wacl'))
>>> ds.properties['dc:title']
'World Atlas of Classifier Languages'
```


## CLI

`cldfzenodo` provides a subcommand to be run from [cldfbench](https://github.com/cldf/cldfbench).
To make use of this command, you have to install `cldfbench`, which can be done via
```shell
pip install cldfzenodo[cli]
```
Then you can download CLDF datasets from Zenodo, using the DOI for identification. E.g.
```shell
cldfbench zenodo.download 10.5281/zenodo.4683137  --directory wals-2020.1/
```
will download WALS Online as CLDF dataset into `wals-2020.1`:
```shell
$ tree wals-2020.1/
wals-2020.1/
├── areas.csv
├── chapters.csv
├── codes.csv
├── contributors.csv
├── countries.csv
├── examples.csv
├── language_names.csv
├── languages.csv
├── parameters.csv
├── sources.bib
├── StructureDataset-metadata.json
└── values.csv

0 directories, 12 files
```


## API

Metadata and data of (potential) CLDF datasets deposited on Zenodo is accessed via `cldfzenodo.Record`
objects. Such objects can be obtained in various ways:
- Via DOI:
  ```python
  import cldfzenodo
  rec = cldfzenodo.Record.from_doi('https://doi.org/10.5281/zenodo.4762034')
  ```
- From deposits grouped into a Zenodo community (and obtained through OAI-PMH):
  ```python
  import cldfzenodo.oai
  for rec in cldfzenodo.oai.iter_records('dictionaria'):
    print(rec)
  ```
- From search results using keywords:
  ```python
  import cldfzenodo
  for rec in cldfzenodo.search_wordlists():
    print(rec)
  ```

`cldfzenodo.Record` objects provide sufficient metadata to allow identification and data access:
```python
>>> from cldfzenodo import Record
>>> print(Record.from_doi('10.5281/zenodo.4762034').bibtex)
@misc{zenodo-4762034,
  author    = {Hammarström, Harald and Forkel, Robert and Haspelmath, Martin and Bank, Sebastian},
  title     = {glottolog/glottolog: Glottolog database 4.4 as CLDF},
  keywords  = {cldf:StructureDataset, linguistics},
  publisher = {Zenodo},
  year      = {2021},
  doi       = {10.5281/zenodo.4762034},
  url       = {https://doi.org/10.5281/zenodo.4762034},
  copyright = {Creative Commons Attribution 4.0}
}
```

One can download the full deposit (and access - possible multiple - CLDF datasets):
```python
from pycldf import iter_datasets

record.download('my_directory')
for cldf in iter_datasets('my_directory'):
    pass
```

But often, only the "pure" CLDF data is of interest - and not the additional metadata and curation
context, e.g. of [cldfbench](https://github.com/cldf/cldfbench)-curated datasets. This can be done
via
```python
cldf = record.download_dataset('my_directory')
```
