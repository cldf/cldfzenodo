from clldutils.misc import deprecated

from cldfzenodo.api import API


def iter_records(keyword, q=None, **kw):
    deprecated('Use `API.iter_records` instead.')
    return API.iter_records(keyword=keyword, allversions=True, _q=q)
