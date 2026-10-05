"""Hidden tests for the model benchmark. The solution path comes from BENCH_SOLUTION."""
import importlib.util
import os

import pytest

spec = importlib.util.spec_from_file_location("solution", os.environ["BENCH_SOLUTION"])
sol = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sol)


@pytest.mark.parametrize("args,expected", [
    ((30, 15, 59.04, "N"), 30.266400),
    ((97, 44, 34.20, "W"), -97.742833),
    ((33, 51, 54.0, "s"), -33.865),
    ((0, 0, 0, "E"), 0.0),
])
def test_dms_valid(args, expected):
    assert sol.dms_to_decimal(*args) == pytest.approx(expected, abs=1e-6)


@pytest.mark.parametrize("args", [(30, 15, 0, "X"), (30, 60, 0, "N"), (30, 0, 60, "N"), (-1, 0, 0, "N")])
def test_dms_invalid(args):
    with pytest.raises(ValueError):
        sol.dms_to_decimal(*args)


@pytest.mark.parametrize("value,expected", [
    ("2019:06:09 17:42:10", ("2019-06-09T17:42:10", False)),
    ("1980:01:01 00:00:00", ("1980-01-01T00:00:00", True)),
    ("2999:01:01 00:00:00", ("2999-01-01T00:00:00", True)),
    (None, (None, False)), ("", (None, False)), ("   ", (None, False)),
    ("0000:00:00 00:00:00", (None, False)), ("not a date", (None, False)), ("2019:13:40 25:00:00", (None, False)),
])
def test_exif_datetime(value, expected):
    assert sol.parse_exif_datetime(value) == expected


@pytest.mark.parametrize("name,expected", [
    ("IMG_20230609_101512.HEIC", "2023-06-09T10:15:12"),
    ("PXL_20220704_201133.jpg", "2022-07-04T20:11:33"),
    (r"D:\PhoneBackups\Mom\WhatsApp\IMG-20210314-WA0007.jpg", "2021-03-14"),
    ("scan_0042.jpg", None),
    ("IMG_20231399_101512.jpg", None),
])
def test_date_from_filename(name, expected):
    assert sol.date_from_filename(name) == expected
