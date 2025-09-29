#!/usr/bin/env python3
"""
Minute Data Gap Report Analyzer (single-file, EST-fixed)
- Parses strict lines: "Gap of <secs>s found between <YYYYMMDDhhmmss> and <YYYYMMDDhhmmss>."
- Buckets (M5-centric): [5–15), [15–30), [30–60), [60–180), [>=180] minutes.
- Treats timestamps as fixed EST (UTC-5, no DST), no conversion to UTC.
- Generates next to the input file:
  * <input>.txt_gap_buckets_by_date.csv
  * <input>.txt_gap_bucket_counts.csv
  * <input>.txt_gaps_scatter.svg   (red points, monthly ticks)
  * <input>.txt_manifest.sha256    (SHA256 of input+outputs; basenames only)
Deterministic outputs: fixed CSV formatting, rcParams for SVG, fixed <dc:date>.
"""

from __future__ import annotations

import argparse
import math
import re
from typing import List, Dict, Any, Tuple

import pandas as pd
import matplotlib as mpl
mpl.rcParams.update({
    "svg.hashsalt": "minute_data_gap_report_analyzer_v1",
    "svg.fonttype": "none",
    "font.family": "DejaVu Sans",
    "axes.formatter.use_locale": False,
})

STRICT_LINE_RE = re.compile(r"^Gap of (\d+)s found between (\d{14}) and (\d{14})\.$")

def _parse_ts_yyyymmddhhmmss(s: str) -> pd.Timestamp:
    # Interpret as fixed EST (UTC-5, no DST) and keep that tz without converting to UTC
    ts = pd.to_datetime(s, format="%Y%m%d%H%M%S")
    return ts.tz_localize("Etc/GMT+5")

def parse_status_report_strict(path: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line_no, raw in enumerate(f, 1):
            line = raw.strip()
            m = STRICT_LINE_RE.match(line)
            if not m:
                continue
            gap_seconds = int(m.group(1))
            start_ts = _parse_ts_yyyymmddhhmmss(m.group(2))
            end_ts = _parse_ts_yyyymmddhhmmss(m.group(3))
            span_seconds = (end_ts - start_ts).total_seconds()
            rows.append(
                {
                    "line_no": line_no,
                    "gap_seconds": gap_seconds,
                    "gap_minutes": gap_seconds / 60.0,
                    "start_est": start_ts,
                    "end_est": end_ts,
                    "span_seconds": span_seconds,
                    "delta_vs_report": span_seconds - gap_seconds,
                }
            )
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("start_est").reset_index(drop=True)
    return df

def add_duration_buckets(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[int], List[str]]:
    bins = [5*60, 15*60, 30*60, 60*60, 180*60, math.inf]
    labels = ["5–15 min", "15–30 min", "30–60 min", "60–180 min", "≥180 min"]
    df = df.copy()
    df["bucket"] = pd.cut(df["gap_seconds"], bins=bins, labels=labels, right=False)
    return df, bins, labels

def compute_bucket_counts(df: pd.DataFrame, labels: List[str]) -> pd.DataFrame:
    bucketed = df.dropna(subset=["bucket"])
    counts = (
        bucketed["bucket"]
        .value_counts()
        .reindex(labels, fill_value=0)
        .rename_axis("bucket").reset_index(name="count")
    )
    total_all = len(df)
    counts["percent_of_all_gaps"] = (counts["count"] / total_all * 100).round(4) if total_all else 0.0
    counts["all_gaps_total"] = total_all
    return counts

def compute_daily_buckets(df: pd.DataFrame, labels: List[str]) -> pd.DataFrame:
    bucketed = df.dropna(subset=["bucket"])
    daily = (
        bucketed.assign(date=bucketed["start_est"].dt.date)
                .groupby(["date", "bucket"], observed=True).size()
                .unstack("bucket")
                .reindex(columns=labels, fill_value=0)
                .reset_index()
                .sort_values("date")
    )
    daily["bucketed_total"] = daily[labels].sum(axis=1)
    all_per_day = df.assign(date=df["start_est"].dt.date).groupby("date").size().rename("all_gaps_total").reset_index()
    daily = daily.merge(all_per_day, on="date", how="left")
    daily["lt_5_min"] = daily["all_gaps_total"] - daily["bucketed_total"]
    cols = ["date"] + labels + ["bucketed_total", "lt_5_min", "all_gaps_total"]
    return daily[cols]

def save_two_csv(df: pd.DataFrame, labels: List[str], outdir: str, prefix: str) -> tuple[str, str]:
    from pathlib import Path
    outdir_path = Path(outdir)
    outdir_path.mkdir(parents=True, exist_ok=True)
    daily = compute_daily_buckets(df, labels)
    path_daily = outdir_path / f"{prefix}_gap_buckets_by_date.csv"
    path_daily.write_text(daily.to_csv(index=False, lineterminator="\n", float_format="%.4f"))
    totals = compute_bucket_counts(df, labels)
    path_totals = outdir_path / f"{prefix}_gap_bucket_counts.csv"
    path_totals.write_text(totals.to_csv(index=False, lineterminator="\n", float_format="%.4f"))
    return str(path_daily), str(path_totals)

def make_scatter_svg_from_daily(daily_df: pd.DataFrame, labels: list[str], out_path: str) -> str:
    """
    Build a scatter SVG: x = date (points spread within day), y = duration bucket (categorical).
    One point per gap (>=5 minutes). Red points, monthly ticks; deterministic IDs.
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from datetime import timedelta
    import re as _re

    df = daily_df.copy()
    df["date"] = pd.to_datetime(df["date"])   # date only; naive ok
    df = df.sort_values("date")

    for lab in labels:
        if lab not in df.columns:
            df[lab] = 0
        df[lab] = pd.to_numeric(df[lab], errors="coerce").fillna(0).astype(int)

    # Подготовка точек
    xs, ys = [], []
    ymap = {lab: i for i, lab in enumerate(labels)}
    for _, row in df.iterrows():
        day = row["date"]
        for lab in labels:
            cnt = int(row[lab])  
            if cnt <= 0:
                continue
            for k in range(cnt):
                frac = (k + 1) / (cnt + 1)      
                t = day + timedelta(seconds=frac * 86400.0)
                xs.append(t.to_pydatetime())
                ys.append(ymap[lab])

    fig = plt.figure(figsize=(12, 5), dpi=100)
    ax = fig.add_subplot(111)
    ax.scatter(xs, ys, s=10, c="red")
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Date (EST, UTC-5 fixed)")
    ax.set_ylabel("Gap duration classification")
    ax.set_title("Gaps (>=5 minutes) — by day and duration bucket (monthly ticks)")

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path, format="svg")
    plt.close(fig)

    with open(out_path, "r", encoding="utf-8") as _f:
        _svg = _f.read()
    _svg = _re.sub(r"<dc:date>.*?</dc:date>", "<dc:date>2000-01-01T00:00:00</dc:date>", _svg, flags=_re.DOTALL)
    with open(out_path, "w", encoding="utf-8", newline="\n") as _f:
        _f.write(_svg)

    return out_path

def sha256_file(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def write_manifest(report_path: str, output_paths: list[str], outdir: str, prefix: str) -> str:
    import os
    from pathlib import Path
    entries = []
    entries.append((os.path.basename(report_path), sha256_file(report_path)))
    for pth in output_paths:
        entries.append((os.path.basename(pth), sha256_file(pth)))
    entries.sort(key=lambda x: x[0])
    out_path = Path(outdir) / f"{prefix}_manifest.sha256"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        for name, digest in entries:
            f.write(f"{digest}  {name}\n")
    return str(out_path)

def main():
    import argparse
    from pathlib import Path

    ap = argparse.ArgumentParser(description="Analyze gap text report and write outputs next to the report (EST fixed).")
    ap.add_argument("report", help="Path to text report file with lines like: 'Gap of 120s found between 20040101120000 and 20040101120130.'")
    args = ap.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        ap.error(f"Report not found: {report_path}")

    df = parse_status_report_strict(str(report_path))
    df, _, labels = add_duration_buckets(df)

    outdir = str(report_path.parent)
    prefix = report_path.name

    out_daily, out_totals = save_two_csv(df, labels, outdir, prefix)

    svg_path = str(Path(outdir) / f"{prefix}_gaps_scatter.svg")
    make_scatter_svg_from_daily(pd.read_csv(out_daily), labels, svg_path)

    outs = [out_daily, out_totals, svg_path]
    manifest_path = write_manifest(str(report_path), outs, outdir, prefix)

    total = len(df)
    bucketed = int(df["bucket"].notna().sum())
    print(f"Parsed gaps: {total} (bucketed >=5min: {bucketed})")
    print("CSVs saved to:")
    print("  -", out_daily)
    print("  -", out_totals)
    print("SVG saved to:")
    print("  -", svg_path)
    print("Manifest:")
    print("  -", manifest_path)

if __name__ == "__main__":
    main()
