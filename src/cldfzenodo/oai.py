"""
Read Zenodo records from OAI PMH feeds for communities.
"""
import xml.etree

from cldfzenodo.record import Record
from cldfzenodo.util import RecordGenerator


class OAIXML(RecordGenerator):
    __base_url__ = "https://zenodo.org/oai2d"

    def __init__(self, text):
        RecordGenerator.__init__(self, text)
        self.xml = xml.etree.ElementTree.fromstring(self.text)

    @staticmethod
    def qn(lname):
        return '{http://www.openarchives.org/OAI/2.0/}%s' % lname

    def iter_records(self):
        for rec in self.xml.findall('.//{}'.format(self.qn('record'))):
            yield Record.from_dcat_element(rec)

    def next(self):
        rt = getattr(self.xml.find('.//{}'.format(self.qn('resumptionToken'))), 'text', None)
        if rt:
            return OAIXML.from_params(verb='ListRecords', resumptionToken=rt)


def iter_records(community):
    for rec in OAIXML.from_params(
            set='user-{0}'.format(community), metadataPrefix='dcat', verb='ListRecords'):
        yield rec
