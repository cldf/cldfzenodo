from cldfbench.__main__ import main


def test_download(tmp_path, mocker):
    class Record:
        def download_dataset(self, dest):
            dest.joinpath('test').write_text('abc', encoding='utf8')

        def download(self, dest):
            dest.joinpath('test').write_text('abc', encoding='utf8')

    class Api:
        def get_record(self, *args, **kw):
            return Record()

    mocker.patch('cldfzenodo.commands.download.API', Api())
    main(['zenodo.download', 'x', '--directory', str(tmp_path)])
    assert tmp_path.joinpath('test').exists()
    main(['zenodo.download', 'x', '--full-deposit', '--directory', str(tmp_path)])
