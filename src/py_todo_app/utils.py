from itertools import chain


def parse_id(id_str: str) -> list[int]:
    match id_str.count("-"):
        case 0:
            return [int(id_str)]
        case 1:
            if id_str.startswith("-"):
                raise ValueError("Negative numbers are not allowed")
            if id_str.endswith("-"):
                raise ValueError("Missing end id in range specification")
            begin, end = (int(i) for i in id_str.split("-", maxsplit=1))

            if begin > end:
                raise ValueError("Range end id cannot be larger than begin id")

            return list(range(begin, end + 1))
        case _:
            raise ValueError("Too many dashes in id range")


def parse_id_set(ids_str: str) -> list[int]:
    """Convert a string of ids in the format "1,2,4-6,8" into a list of ids

    Different ids are separated by commas, which may be single numbers for a
    single id, or a pair following the format ``X-Y``, which represents the range
    from X up to and including Y. Example::

    parse_id_string("1,2,4-6,8") == [1, 2, 4, 5, 6, 8]"""

    if ids_str.startswith(","):
        raise ValueError("Unexpected comma at beginning of id set")
    if ids_str.endswith(","):
        raise ValueError("Unexpected comma at end of id set")
    if ",," in ids_str:
        raise ValueError("Unexpected comma in middle of id set")

    id_gen = (parse_id(ids) for ids in ids_str.split(",") if ids)
    ids = sorted(set(chain.from_iterable(id_gen)))

    return ids
