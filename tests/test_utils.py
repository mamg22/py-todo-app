import re

import pytest

from py_todo_app.utils import parse_id, parse_id_set


def test_parse_id():
    assert parse_id("1") == [1]
    assert parse_id("1-3") == [1, 2, 3]
    assert parse_id("1-31") == list(range(1, 32))


def test_parse_id_invalid():
    invalid_int_exc = re.escape("invalid literal for int() with base 10: 'invalid'")
    with pytest.raises(ValueError, match=invalid_int_exc):
        parse_id("invalid")

    with pytest.raises(ValueError, match=invalid_int_exc):
        parse_id("3-invalid")

    with pytest.raises(ValueError, match="Negative numbers are not allowed"):
        parse_id("-1")

    with pytest.raises(ValueError, match="Missing end id in range specification"):
        parse_id("1-")

    with pytest.raises(ValueError, match="Too many dashes in id range"):
        parse_id("1--2")

    with pytest.raises(ValueError, match="Range end id cannot be larger than begin id"):
        parse_id("3-1")


def test_parse_id_set():
    assert parse_id_set("1-3") == [1, 2, 3]
    assert parse_id_set("1,2,3") == [1, 2, 3]
    assert parse_id_set("1,3-5,7") == [1, 3, 4, 5, 7]
    assert parse_id_set("1,2,2,4-6,6") == [1, 2, 4, 5, 6]


def test_parse_id_set_invalid():
    with pytest.raises(ValueError, match="Unexpected comma at beginning of id set"):
        parse_id_set(",1-3")

    with pytest.raises(ValueError, match="Unexpected comma at end of id set"):
        parse_id_set("1,2,")

    with pytest.raises(ValueError, match="Unexpected comma in middle of id set"):
        parse_id_set("1,,3")
