Write a single Python 3.11 file at the path given below. Use only the standard library.
Write that one file and nothing else; do not read other files.

Implement these three functions for a photo-library app:

1. `dms_to_decimal(degrees: float, minutes: float, seconds: float, ref: str) -> float`
   Convert GPS degrees/minutes/seconds to decimal degrees, rounded to 6 decimal places.
   `ref` is "N", "S", "E" or "W" (case-insensitive); "S" and "W" give negative values.
   Raise ValueError for any other ref, for minutes or seconds outside 0 to <60, or for negative degrees.

2. `parse_exif_datetime(value: str | None) -> tuple[str | None, bool]`
   EXIF dates look like "2019:06:09 17:42:10". Return (iso, suspect) where iso is
   "YYYY-MM-DDTHH:MM:SS". Return (None, False) for None, empty, whitespace,
   "0000:00:00 00:00:00" or any malformed value. suspect is True when the year is before 1990
   or the date is later than the current date and time.

3. `date_from_filename(name: str) -> str | None`
   Recover a date from common phone file names (any folder prefix may be present):
   "IMG_20230609_101512.HEIC" and "PXL_20220704_201133.jpg" -> "2023-06-09T10:15:12" / "2022-07-04T20:11:33";
   "IMG-20210314-WA0007.jpg" (WhatsApp) -> "2021-03-14" (date only).
   Return None when no valid date is found (including impossible dates like 20231399).
