"""Reference solution, used only to validate the hidden tests (never shown to the models)."""
import re
from datetime import datetime


def dms_to_decimal(degrees, minutes, seconds, ref):
    ref = str(ref).upper()
    if ref not in ("N", "S", "E", "W"):
        raise ValueError(f"invalid ref {ref}")
    if degrees < 0 or not 0 <= minutes < 60 or not 0 <= seconds < 60:
        raise ValueError("out of range")
    value = degrees + minutes / 60 + seconds / 3600
    return round(-value if ref in ("S", "W") else value, 6)


def parse_exif_datetime(value):
    if not value or not value.strip():
        return None, False
    try:
        dt = datetime.strptime(value.strip(), "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None, False
    return dt.strftime("%Y-%m-%dT%H:%M:%S"), dt.year < 1990 or dt > datetime.now()


def date_from_filename(name):
    base = re.split(r"[\\/]", name)[-1]
    m = re.search(r"(?:IMG|PXL)_(\d{8})_(\d{6})", base)
    if m:
        try:
            return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S").strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None
    m = re.search(r"IMG-(\d{8})-WA\d+", base)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y%m%d").strftime("%Y-%m-%d")
        except ValueError:
            return None
    return None
