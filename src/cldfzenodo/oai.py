"""
Read Zenodo records from OAI PMH feeds for communities.
"""
from clldutils import oaipmh

from cldfzenodo.record import Record

__all__ = ['iter_records']


def iter_records(community):
    for rec in oaipmh.iter_records(
            "https://zenodo.org/oai2d", metadataPrefix='dcat', set_='user-{0}'.format(community)):
        yield Record.from_dcat_element(rec.metadata)
