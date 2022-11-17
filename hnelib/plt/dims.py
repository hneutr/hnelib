import itertools

"""
Nature guidelines on widths:
- 1 col: 89mm
- 1.5 col:
- small: 120mm
- medium: 128mm
- large: 136mm
- 2 col: 183mm
"""
MMS = {
    '.5': 44,
    '1': 89,
    '1.5': 136,
    "1.5s": 120,
    "1.5m": 128,
    "1.5l": 136,
    '2': 183,
}


D = {}


__MMS_PER_INCH__ = 25.4


def __mm_to_inch__(mms):
    return round(mms / __MMS_PER_INCH__, 2)


def __setup__():
    global MMS, D

    D = {k: __mm_to_inch__(v) for k, v in MMS.items()}

    # sizes = list(D.keys())
    for k_w, k_h in itertools.product(D, D):
        D[f"{k_w}, {k_h}"] = (D[k_w], D[k_h])


if not len(D):
    __setup__()
