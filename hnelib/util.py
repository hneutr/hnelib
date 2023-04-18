ONES_TO_WORD = {
    '0': 'zero',
    '1': 'one',
    '2': 'two',
    '3': 'three',
    '4': 'four',
    '5': 'five',
    '6': 'six',
    '7': 'seven',
    '8': 'eight',
    '9': 'nine',
}

TEENS_TO_WORD = {
    '10': 'ten',
    '11': 'eleven',
    '12': 'twelve',
    '13': 'thirteen',
    '14': 'fourteen',
    '15': 'fifteen',
    '16': 'sixteen',
    '17': 'seventeen',
    '18': 'eighteen',
    '19': 'nineteen',
}

IRREGULAR_TENS_TO_WORD = {
    '20': 'twenty',
    '30': 'thirty',
    '40': 'forty',
    '50': 'fifty',
    '60': 'sixty',
    '70': 'seventy',
    '80': 'eighty',
    '90': 'ninety',
}

NUMBER_TO_WORD = {
    **ONES_TO_WORD,
    **TEENS_TO_WORD,
    **IRREGULAR_TENS_TO_WORD,
}

DIGIT_COUNT_TO_WORD = {
    3: 'hundred',
    4: 'thousand',
    7: 'million',
    10: 'trillion',
    13: 'billion',
}


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
    import numpy as np

    if thing is None:
        thing = []
    elif isinstance(thing, pd.Series):
        thing = list(thing)
    elif isinstance(thing, np.ndarray):
        thing = thing.flatten()
    elif not isinstance(thing, list):
        thing = [thing]

    return thing


def as_element(thing):
    """
    turns a list into an element if possible

    `thing` should be a list

    returns:
    - if len(thing) == 1: thing[0]
    - else: thing
    """
    if len(thing) == 1:
        thing = thing[0]

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
        return strings[0]

    return strings


def number_to_words(number, include_digit_count_words=True):
    number_str = str(number)
    decimal_str = ""

    if '.' in number_str:
        number_str, decimal_str = number_str.split('.')

    parts = []

    if number_str.startswith('-'):
        number_str = number_str[1:]
        parts.append('negative')

    while number_str:
        current_str = number_str[0]
        next_str = number_str[1:]

        if len(number_str) == 2:
            if number_str[:2] in TEENS_TO_WORD:
                current_str = number_str[:2]
                next_str = number_str[2:]
            elif current_str != '0':
                current_str += '0'

        current_word = NUMBER_TO_WORD[current_str]

        if current_str != '0' or not parts:
            parts.append(current_word)

        if parts[-1] not in list(DIGIT_COUNT_TO_WORD.values()):
            parts.append(DIGIT_COUNT_TO_WORD.get(len(number_str)))

            if len(next_str) == 2:
                parts.append("and")

        number_str = next_str

    parts = [p for p in parts if p]

    if not include_digit_count_words:
        last_part = parts[-1]
        parts = [p for p in parts if p not in ["and"] + list(DIGIT_COUNT_TO_WORD.values())]

        if last_part in list(DIGIT_COUNT_TO_WORD.values()):
            parts.append(last_part)

    if decimal_str:
        parts.append("point")
        parts += [NUMBER_TO_WORD[d] for d in decimal_str]


    return " ".join(parts)
