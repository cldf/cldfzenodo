from cldfbench.__main__ import main


def test_download(tmp_path, mocker):
    mocker.patch('cldfzenodo.commands.download.Record', mocker.Mock())
    main(['zenodo.download', 'x', '--directory', str(tmp_path)])
