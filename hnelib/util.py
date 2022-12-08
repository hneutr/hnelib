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


def as_list(thing=None):
    """
    makes a thing into a list.

    - pd.Series → list
    - None → []
    - thing = 7 → [7]
    """
    import pandas as pd

    if thing is None:
        thing = []
    elif isinstance(thing, pd.Series):
        thing = list(thing)
    elif isinstance(thing, np.ndarray):
        thing = thing.flatten()
    elif not isinstance(thing, list):
        thing = [thing]

    return thing

def num_to_pretty_str(numbers):
    numbers = as_list(numbers)

    strings = []
    for number in numbers:
        string = str(number)

        prefix = ''
        if '-' in string:
            string = string.replace('-', '')
            prefix = '-'

        if '.' in string:
            string, decimal_part = str(string).split('.')

            if decimal_part == "0" and string == "0":
                string = "0"
            else:
                string = "." if string == "0" else f"{string}"

            if decimal_part != '0':
                if '.' not in string:
                    string += '.'

                string += f'{decimal_part}'

        string = prefix + string

        strings.append(string)

    if len(strings) == 1:
        strings = [strings[0]]

    return strings
