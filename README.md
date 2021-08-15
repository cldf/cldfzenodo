# cldfzenodo

[![Build Status](https://github.com/cldf/cldfzenodo/workflows/tests/badge.svg)](https://github.com/cldf/cldfzenodo/actions?query=workflow%3Atests)
[![PyPI](https://img.shields.io/pypi/v/cldfzenodo.svg)](https://pypi.org/project/cldfzenodo)

`cldfzenodo` provides programmatic access to CLDF data deposited on [Zenodo](https://zenodo.org).


## Install

```shell
pip install cldfzenodo
```


## Usage

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

`cldfzenodo.Record` objects provide sufficient metadata to allow identification and data access.
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
from pycldf import Dataset
mdpath = record.download_dataset('my_directory')
cldf = Dataset.from_metadata(mdpath)
```
