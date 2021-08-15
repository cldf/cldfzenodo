import pathlib
import xml.etree

import pytest


@pytest.fixture
def tests_dir():
    return pathlib.Path(__file__).parent


@pytest.fixture
def dcat_record(tests_dir):
    return tests_dir.joinpath('dcat_record.xml').read_text(encoding='utf8')


@pytest.fixture
def dcat_record_element(dcat_record):
    return xml.etree.ElementTree.fromstring(dcat_record)