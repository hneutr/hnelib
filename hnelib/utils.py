import pandas as pd

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


def add_ordinal_indicator(string):
    if string.isnumeric():
        ones_pos = int(string[0])

        if ones_pos == 1:
            indicator = "st"
        elif ones_pos == 2:
            indicator = "nd"
        elif ones_pos == 3:
            indicator = "rd"
        else:
            indicator = "th"

        string += indicator
    
    return string


def listify(thing):
    thing = thing or []

    if not isinstance(thing, list):
        thing = [thing]

    return thing
