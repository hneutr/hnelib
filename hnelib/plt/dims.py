"""
Nature guidelines on widths:
- 1 col: 89mm
- 1.5 col:
    - small: 120mm
    - medium: 128mm
    - large: 136mm
- 2 col: 183mm
"""
import itertools
import functools

DIMS_IN_MMS = {
    .5: 44,
    1: 89,
    1.5: 136,
    2: 183,
    # "1.5s": 120,
    # "1.5m": 128,
    # "1.5l": 136,
}


MMS_PER_INCH = 25.4


def __mms_to_inch__(mms):
    return round(mms / MMS_PER_INCH, 2)


@functools.lru_cache
def __get_dims__():
    dims = {k: __mms_to_inch__(v) for k, v in DIMS_IN_MMS.items()}

    # sizes = list(D.keys())
    for k_w, k_h in itertools.product(dims, dims):
        dims[(k_w, k_h)] = (dims[k_w], dims[k_h])

    return dims


dims = __get_dims__()
