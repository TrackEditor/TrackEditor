import hashlib


def md5sum(file: str) -> str:
    md5_hash = hashlib.md5()

    a_file = open(file, "rb")
    content = a_file.read()
    md5_hash.update(content)

    digest = md5_hash.hexdigest()

    return digest


def print_progress_bar(iteration: int, total: int,
                       prefix: str = '', suffix: str = '', decimals: int = 1,
                       length: int = 100, fill: str = '|'):
    """
    Call in a loop to create terminal progress bar
    :param iteration: current iteration
    :param total: total iterations
    :param prefix: prefix string
    :param suffix: suffix string
    :param decimals: positive number of decimals in percent complete
    :param length: character length of bar
    :param fill: bar fill character
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                            (float(iteration) / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length - 1)

    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='')
