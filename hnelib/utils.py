import pandas as pd
from scipy.stats import pearsonr

def empty_directory(directory, recursive=True, delete=True):
    for f in directory.glob('*'):
        if f.is_file():
            f.unlink()
        elif recursive:
            empty_directory(f)
            f.rmdir()

    if delete and not len(list(directory.glob('*'))):
        directory.rmdir()

def fraction_to_percent(fraction, round_to=0):
    percent = 100 * fraction
    if round_to != None:
        percent = round(percent, round_to)

        if round_to == 0:
            percent = int(percent)

    return percent


def series_to_list(thing):
    if isinstance(thing, pd.Series):
        thing = list(thing)

    return thing



def correlation(xs, ys):
    pearson, pearson_p = pearsonr(xs, ys)
    return pearson, pearson_p
