import utils


def test_md5sum(tmp_path):
    tmp_file = tmp_path / 'test_md5sum.txt'
    tmp_file.write_text('')

    assert utils.md5sum(tmp_file) == 'd41d8cd98f00b204e9800998ecf8427e'


def test_moving_average():
    testing = [1, 2, 3, 4, 5, 6]
    expected = [(1+2+3)/3,
                (2+3+4)/3,
                (3+4+5)/3,
                (4+5+6)/3]

    assert all(utils.moving_average(testing) == expected)


def test_print_progress_bar(capsys):
    # Empty bar
    utils.print_progress_bar(0, 100, length=20)
    captured = capsys.readouterr()
    assert captured.out == '\r |-------------------| 0.0% '

    # Medium bar
    utils.print_progress_bar(50, 100, length=20)
    captured = capsys.readouterr()
    assert captured.out == '\r |||||||||||---------| 50.0% '

    # Full bar
    utils.print_progress_bar(100, 100, length=20)
    captured = capsys.readouterr()
    assert captured.out == '\r |||||||||||||||||||||| 100.0% '
