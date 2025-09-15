import csv
import os
import sys
import argparse
from datetime import datetime
from dateutil import tz as dttz      # pip install python-dateutil
from dateutil import parser as dparser
# tzdata must be installed and pinned for deterministic rules (pip install tzdata==2025.2)

FMT_MIN = "%Y-%m-%dT%H:%M"
FMT_SEC = "%Y-%m-%dT%H:%M:%S"

US_ZONES = {
    "America/New_York","America/Chicago","America/Denver","America/Los_Angeles",
    "America/Phoenix","America/Anchorage","Pacific/Honolulu",
    "America/Detroit","America/Indiana/Indianapolis","America/Indiana/Knox","America/Kentucky/Louisville",
}
EUROZONE_ZONES = {
    "Europe/Amsterdam","Europe/Brussels","Europe/Berlin","Europe/Paris","Europe/Madrid","Europe/Rome",
    "Europe/Vienna","Europe/Luxembourg","Europe/Dublin","Europe/Lisbon","Atlantic/Madeira",
    "Europe/Helsinki","Europe/Athens","Europe/Bratislava","Europe/Ljubljana","Europe/Tallinn","Europe/Riga",
    "Europe/Vilnius","Europe/Malta","Asia/Nicosia",
}
ALLOWED_ZONES = US_ZONES | EUROZONE_ZONES

# ---------- parsing helpers ----------

_EXPLICIT_PATTERNS = [
    # ISO-like
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M",
    # US-style with slashes
    "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M",
    "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %I:%M %p",
    # EU-style with slashes (day-first)
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M",
    "%d/%m/%Y %I:%M:%S %p", "%d/%m/%Y %I:%M %p",
    # EU-style with dots
    "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M",
    "%d.%m.%Y %I:%M:%S %p", "%d.%m.%Y %I:%M %p",
]

def _parse_explicit(s: str):
    for fmt in _EXPLICIT_PATTERNS:
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None

def parse_local_dt(s: str, tz_hint: str | None) -> datetime:
    """
    Parse local wall time from various common formats.
    - Tries explicit known patterns first.
    - Falls back to dateutil.parser with yearfirst and dayfirst inferred from tz_hint:
        * US zones -> dayfirst=False
        * Eurozone -> dayfirst=True
    Returns naive datetime (no tzinfo).
    """
    s = (s or "").strip()
    if not s:
        raise ValueError("local_dt is empty")

    # 1) try explicit formats (fast & unambiguous)
    dt = _parse_explicit(s)
    if dt is not None:
        if dt.tzinfo is not None:
            raise ValueError("local_dt must be a local wall time without offset/tzinfo")
        return dt

    # 2) fallback: dateutil parser
    dayfirst = False
    if tz_hint in EUROZONE_ZONES:
        dayfirst = True
    elif tz_hint in US_ZONES:
        dayfirst = False
    # If tz_hint is unknown/None, default to yearfirst=True and dayfirst=False (safer for US-style)
    try:
        parsed = dparser.parse(s, yearfirst=True, dayfirst=dayfirst, fuzzy=False)
    except Exception as e:
        raise ValueError(
            f"Invalid local_dt format: {s!r}. "
            f"Accepted examples: 'YYYY-MM-DD HH:MM[:SS]', 'YYYY-MM-DDTHH:MM[:SS]', "
            f"'MM/DD/YYYY HH:MM', 'DD/MM/YYYY HH:MM', 'DD.MM.YYYY HH:MM', with or without seconds."
        ) from e
    if parsed.tzinfo is not None:
        # We expect local wall time without tzinfo/offset. If input carried an offset,
        # reject to avoid double-applying zone rules. (Safer for auditability.)
        raise ValueError("local_dt must not include an explicit offset (e.g. '+02:00' or 'Z')")
    return parsed

# ---------- conversion ----------

def to_utc_iso_seconds(local_dt_str: str, source_tz: str,
                       ambiguous: str = "latest", nonexistent: str = "shift_forward") -> str:
    """
    Convert local wall time + IANA zone to UTC with seconds and '+00:00' offset.
    - ambiguous: 'earliest' | 'latest' | 'raise'
    - nonexistent: 'shift_forward' | 'raise'
    """
    tzinfo = dttz.gettz(source_tz)
    if tzinfo is None:
        raise ValueError(f"Invalid IANA timezone: {source_tz!r}")
    naive = parse_local_dt(local_dt_str, source_tz)
    aware = naive.replace(tzinfo=tzinfo)

    # Spring-forward gap (nonexistent local times)
    if not dttz.datetime_exists(aware):
        if nonexistent == "raise":
            raise ValueError(f"Nonexistent local time due to DST gap: {local_dt_str} in {source_tz}")
        aware = dttz.resolve_imaginary(aware)

    # Fall-back overlap (ambiguous local times)
    if dttz.datetime_ambiguous(aware):
        if ambiguous == "raise":
            raise ValueError(f"Ambiguous local time at DST fall-back: {local_dt_str} in {source_tz}")
        fold = 0 if ambiguous == "earliest" else 1
        aware = dttz.enfold(aware, fold=fold)

    return aware.astimezone(dttz.UTC).isoformat(timespec="seconds")

# ---------- main pipeline ----------

def normalize_file(in_path: str, out_path: str | None,
                   ambiguous: str, nonexistent: str, allow_any_zones: bool) -> str:
    in_path = os.path.abspath(in_path)
    if not os.path.exists(in_path):
        raise FileNotFoundError(f"Input file not found: {in_path}")
    root, ext = os.path.splitext(in_path)
    out_path = os.path.abspath(out_path) if out_path else f"{root}_UTC{ext or '.csv'}"

    # Read (UTF-8; tolerate BOM). Separator is ';'.
    with open(in_path, "r", encoding="utf-8-sig", newline="") as fi:
        reader = csv.DictReader(fi, delimiter=";")
        fields = reader.fieldnames or []
        if "local_dt" not in fields or "source_tz" not in fields:
            raise ValueError(f"CSV must contain 'local_dt' and 'source_tz'. Found: {fields}")
        non_time = [c for c in fields if c not in ("local_dt", "source_tz", "datetime_utc")]

        # Place datetime_utc immediately AFTER 'event'
        if "event" in non_time:
            i = non_time.index("event") + 1
            out_fields = non_time[:i] + ["datetime_utc"] + non_time[i:]
        else:
            out_fields = non_time + ["datetime_utc"]

        rows_out = []
        for irow, row in enumerate(reader, start=1):
            tz = row.get("source_tz", "")
            if (not allow_any_zones) and tz not in ALLOWED_ZONES:
                raise ValueError(f"Row {irow}: source_tz '{tz}' not in US/Eurozone allow-list "
                                 f"(use --allow-any-zones to bypass)")
            dt_utc = to_utc_iso_seconds(row.get("local_dt",""), tz, ambiguous=ambiguous, nonexistent=nonexistent)
            data = {k: row.get(k, "") for k in non_time}
            assembled = {}
            for k in out_fields:
                assembled[k] = dt_utc if k == "datetime_utc" else data.get(k, "")
            rows_out.append(assembled)

    # Sort ascending by datetime_utc (ISO UTC strings are lexicographically sortable)
    rows_out.sort(key=lambda r: r["datetime_utc"])

    # Write deterministically: UTF-8 (no BOM), ';' separator, LF endings
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as fo:
        writer = csv.DictWriter(fo, fieldnames=out_fields, delimiter=';', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows_out)

    return out_path

def main():
    ap = argparse.ArgumentParser(description="Convert calendar CSV to UTC and sort by datetime_utc.")
    ap.add_argument("in_csv", help="Input CSV path with ';' separator; requires columns: local_dt, source_tz")
    ap.add_argument("out_csv", nargs="?", help="Output CSV path; defaults to <in>_UTC.csv")
    ap.add_argument("--ambiguous", choices=["earliest","latest","raise"], default="latest",
                    help="How to resolve DST fall-back overlap (default: latest)")
    ap.add_argument("--nonexistent", choices=["shift_forward","raise"], default="shift_forward",
                    help="How to resolve DST spring-forward gap (default: shift_forward)")
    ap.add_argument("--allow-any-zones", action="store_true",
                    help="Bypass US/Eurozone allow-list for source_tz")
    args = ap.parse_args()
    try:
        out = normalize_file(args.in_csv, args.out_csv, args.ambiguous, args.nonexistent, args.allow_any_zones)
    except Exception as e:
        sys.exit(f"[ERR] {e}")
    print(out)

if __name__ == "__main__":
    main()