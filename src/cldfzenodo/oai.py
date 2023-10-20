from clldutils.misc import deprecated

from cldfzenodo.api import API


def iter_records(community):
    deprecated('Use `API.iter_records` instead.')
    return API.iter_records(community=community, allversions=True)
