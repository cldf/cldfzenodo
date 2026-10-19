import logging
import argparse

import pytest


@pytest.mark.parametrize(
    "args,assertion",
    [
        (["x"], lambda d: d.joinpath("test").exists()),
        (["x", "--version-tag", "v1"], None),
        (["x", "--full-deposit"], None),
    ],
)
def test_download(args, assertion, tmp_path, mocker, recwarn):
    from cldfzenodo.commands.download import register, run
    class Record:
        def download_dataset(self, dest):
            dest.joinpath("test").write_text("abc", encoding="utf8")

        def download(self, dest):
            dest.joinpath("test").write_text("abc", encoding="utf8")

    class Api:
        def get_record(self, *args, **kw):
            return Record()

    mocker.patch("cldfzenodo.commands.download.API", Api())
    parser = argparse.ArgumentParser()
    register(parser)
    run(parser.parse_args(args + ["--directory", str(tmp_path)]))
    if assertion:
        assert assertion(tmp_path)


def test_upload(fixtures_dir, mocker, capsys, caplog):
    from cldfzenodo.commands.upload import register, run
    def put(url, **kw):
        print(url)
        return mocker.Mock(status_code=201)

    mocker.patch("cldfzenodo.commands.upload.API", lambda *_, **kw: '{"links":{"bucket":"bucket"}}')
    mocker.patch("cldfzenodo.commands.upload.requests.put", put)
    mocker.patch("cldfzenodo.commands.upload.os.environ", {"TOKEN": "x"})

    parser = argparse.ArgumentParser()
    register(parser)
    args = parser.parse_args(["did", str(fixtures_dir), "TOKEN"])
    args.log = logging.getLogger(__name__)
    with caplog.at_level(logging.INFO):
        run(args)
    out, _ = capsys.readouterr()
    assert 'bucket' in out
    assert 'communities.json' in out
    assert len(caplog.records) == 6
