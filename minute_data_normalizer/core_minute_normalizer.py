# -*- coding: utf-8 -*-
"""
Minute Data Normalizer — one-file module (minute_data_normalizer/cli.py).

Run example (macOS/Linux, from inside minute_data_normalizer/ folder):
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install -r requirements.lock  # install environment
  PYTHONPATH=.. python -m minute_data_normalizer.cli normalize --input ./DAT_ASCII_EURUSD_M1_2024.csv

Rules (unchanged):
- Input: CSV only (delimiter ';').
- Headers: datetime;open;high;low;close;volume (if input is headerless DAT_ASCII).
- Time conversion: fixed EST (UTC-5, no DST) -> UTC.
- Datetime output format: YYYY-MM-DDTHH:MM (no seconds, 'T' separator).
- Sorting: ascending by time (stable). No gap-filling, no dedup.
- OHLCV are treated as plain text: not modified/rounded/reformatted.
- Output CSV: ';' delimiter, UTF-8, '\n' line endings, no gzip.
- Output name: <input_stem>_UTC.csv unless --output is provided (forced .csv).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd
from dateutil.tz import tzoffset


# Detect headerless DAT_ASCII: "YYYYMMDD HHMMSS;Open;High;Low;Close;Volume"
# Also allow "YYYYMMDDHHMMSS;..."
_DAT_ASCII_PATTERN = re.compile(r"^[0-9]{8}\s?[0-9]{6}[;,\t]")

# Fixed EST (no DST): UTC-5
_FIXED_EST = tzoffset(None, -5 * 3600)

# Supported strict input datetime formats
_IN_FORMATS = ("%Y%m%d %H%M%S", "%Y%m%d%H%M%S")

# Output datetime format (UTC)
_OUT_FORMAT = "%Y-%m-%dT%H:%M"


def _is_dat_ascii_first_line(line: str) -> bool:
    return bool(_DAT_ASCII_PATTERN.match(line.strip()))


def _load_csv(input_path: str | Path, *, delimiter: str | None = None, encoding: str = "utf-8") -> pd.DataFrame:
    """Load minute data from CSV (only). Keep OHLCV as strings (do not alter numeric text)."""
    path = Path(input_path)
    if path.suffix.lower() != ".csv":
        raise SystemExit("Error: input must be a .csv file")

    with path.open("r", encoding=encoding, errors="replace") as f:
        first_line = f.readline()

    if _is_dat_ascii_first_line(first_line):
        sep = delimiter or ";"
        names = ["datetime", "open", "high", "low", "close", "volume"]
        df = pd.read_csv(path, sep=sep, header=None, names=names, encoding=encoding, engine="python", dtype=str)
        return df

    # Fallback: CSV with header; read all as strings
    df = pd.read_csv(path, sep=(delimiter if delimiter else None), engine="python", encoding=encoding, dtype=str)

    # Try to normalize datetime column name if present under an alias
    for cand in ("datetime", "timestamp", "dt", "time"):
        if cand in df.columns and "datetime" not in df.columns:
            df = df.rename(columns={cand: "datetime"})
            break

    return df


def _parse_datetime_series(s: pd.Series) -> pd.Series:
    # Try strict formats first
    parsed = None
    for fmt in _IN_FORMATS:
        try:
            parsed = pd.to_datetime(s, format=fmt, errors="raise")
            break
        except Exception:
            parsed = None
    if parsed is None:
        parsed = pd.to_datetime(s, errors="coerce")
    if parsed.isna().any():
        bad = int(parsed.isna().sum())
        raise SystemExit(f"Error: failed to parse {bad} datetime values")
    return parsed


def _normalize_minutes(df: pd.DataFrame, *, sort: bool = True) -> pd.DataFrame:
    """Convert fixed EST -> UTC, format datetime, stable sort. No gap-filling, no dedup."""
    required = ["datetime", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"Error: missing required columns: {missing}")

    out = df.copy()

    # Parse local fixed EST -> UTC (tz-aware), then drop tz and format
    dt_local = _parse_datetime_series(out["datetime"]).dt.tz_localize(_FIXED_EST)
    dt_utc = dt_local.dt.tz_convert("UTC")

    if sort:
        order = dt_utc.argsort(kind="mergesort")
        out = out.iloc[order].reset_index(drop=True)
        dt_utc = dt_utc.iloc[order].reset_index(drop=True)

    out["datetime"] = dt_utc.dt.tz_localize(None).dt.strftime(_OUT_FORMAT)

    # Return in exact column order; OHLCV remain as text
    return out[required]


def _derive_output_csv_path(input_path: str | Path, output_arg: str | None) -> Path:
    """Same name + '_UTC' suffix (forced .csv) unless --output is supplied."""
    in_p = Path(input_path)
    if output_arg:
        out_p = Path(output_arg)
        if out_p.suffix.lower() != ".csv":
            out_p = out_p.with_suffix(".csv")
        return out_p
    return in_p.with_name(f"{in_p.stem}_UTC.csv")


def _write_csv(df, path, *, sep=";", encoding="utf-8"):

    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    csv_bytes = df.to_csv(sep=sep, index=False, lineterminator="\n").encode(encoding)
    with open(path, "wb") as f:
        f.write(csv_bytes)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python core_minute_normalizer.py",
        description="Minute data normalizer (one-file)"
    )

    p.add_argument("--input",      required=False, help="Input CSV file path (.csv only)")
    p.add_argument("--output",     default=None)
    p.add_argument("--delimiter",  default=None)
    p.add_argument("--encoding",   default="utf-8")
    p.add_argument("--report",     default=None)
    p.add_argument("--stats-json", default=None)


    sub = p.add_subparsers(dest="command", required=False)

    p_ver = sub.add_parser("version", help="Show version and exit")
    p_ver.set_defaults(func=lambda args: print("0.0.1"))

    p_norm = sub.add_parser("normalize", help="Normalize minutes: headers + EST->UTC + sort")
    p_norm.add_argument("--input", required=True, help="Input CSV file path (.csv only)")
    p_norm.add_argument("--output", default=None)
    p_norm.add_argument("--delimiter", default=None)
    p_norm.add_argument("--encoding", default="utf-8")
    p_norm.add_argument("--report", default=None)
    p_norm.add_argument("--stats-json", default=None)
    p_norm.set_defaults(func=_cmd_normalize)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "command", None) is None:
        if not args.input:
            parser.error("--input is required (или используйте подкоманду 'normalize')")
        return _cmd_normalize(args) or 0
    return args.func(args) or 0


def _cmd_normalize(args: argparse.Namespace) -> int:
    in_path = Path(args.input)
    df = _load_csv(in_path, delimiter=(args.delimiter or ";"), encoding=args.encoding)
    out_df = _normalize_minutes(df, sort=True)

    out_path = _derive_output_csv_path(in_path, args.output)
    _write_csv(out_df, out_path, sep=";", encoding="utf-8")

    if args.report or args.stats_json:
        dt_min = str(out_df["datetime"].min())
        dt_max = str(out_df["datetime"].max())
        text = (
            f"Input file: {in_path}\n"
            f"Output file: {out_path}\n"
            f"Rows: {len(out_df)}\n"
            f"Range (UTC): {dt_min} -> {dt_max}\n"
            f"Gaps: preserved (no synthetic bars), no dedup.\n"
        )
        if args.report:
            Path(args.report).write_text(text, encoding="utf-8")
        if args.stats_json:
            stats = {
                "input_file": str(in_path),
                "output_file": str(out_path),
                "rows": len(out_df),
                "datetime_min_utc": dt_min,
                "datetime_max_utc": dt_max,
                "gaps_policy": "preserved",
                "dedup": False,
            }
            Path(args.stats_json).write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
  
    if getattr(args, "command", None) is None:
        if not args.input:
            parser.error("--input is required (or use 'normalize' command)")
        return _cmd_normalize(args) or 0
    return args.func(args) or 0


if __name__ == "__main__":
    raise SystemExit(main())
