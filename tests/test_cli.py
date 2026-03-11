import argparse

import pytest

from cldfzenodo.commands.download import register, run


@pytest.mark.parametrize(
    "args,assertion",
    [
        (["x"], lambda d: d.joinpath("test").exists()),
        (["x", "--version-tag", "v1"], None),
        (["x", "--full-deposit"], None),
    ],
)
def test_download(args, assertion, tmp_path, mocker, recwarn):
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
