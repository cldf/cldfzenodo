# Changes

## unreleased

- Make all metadata from Zenodo available from a `Record` instance.


## [2.1.2] - 2024-10-15

- Fix to accomodate change in Zenodo's communities search API.
- Run tests on py 3.13.


## [2.1.1] - 2024-03-05

- Make `version_tag` argument to `from_concept_doi` optional, to make it more transparent
  that this is the method to call to get the latest version for a concept DOI.


## [2.1.0] - 2023-11-27

- Add Python 3.12 to supported versions.
- Added API method to retrieve release information from GitHub/Zenodo.


## [2.0.0] - 2023-10-20

Zenodo's upgrade from Oct. 13, 2023 brought a couple of breaking changes for the Zenodo API.
While it was possible to accomodate these changes in the implementation of `cldfzenodo`, while
keeping the **cldfzenodo** API as is, we took the opportunity to also add a streamlined API. This
only affects the `cldfzenodo` Python API, though - the commandline interface 
`cldfbench zenodo.download`, as well as the `DatasetResolver` functionality has not
changed. The old Python API is still available, though, but using it will trigger deprecation
warnings.

Deprecated functionality will be removed in v2.2.


### Other changes

- Dropped py3.7 compatibility.


## [1.1.0] - 2022-12-21

- Added support for retrieval of versioned datasets via concept DOI and version tag.
- Added support for downloading full deposits via CLI.


## [1.0.0] - 2022-11-22

First feature-complete release

