#!/usr/bin/env python3
import csv
import glob
import html
import os
import shutil
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

csv.field_size_limit(10**7)

METRICS = [
    ("deconv_c0_mean", 1),
    ("deconv_c1_mean", 1),
    ("deconv_c2_mean", 1),
    ("grayscale_brightness", -1),
    ("rms_contrast", 1),
]
REVIEW_COUNT = 40


def number(value):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return np.nan
    return v if np.isfinite(v) else np.nan


def faint_scores(values, direction):
    median = np.nanmedian(values)
    spread = 1.4826 * np.nanmedian(np.abs(values - median))
    if not spread:
        return np.full(len(values), np.nan)
    return -direction * (values - median) / spread


def review_section(metric, rows, values, label, order):
    cards = []
    for i in order:
        name = html.escape(rows[i]["name"])
        cards.append(
            f'<figure><img loading="lazy" src="thumbs/{name}.jpg" alt="">'
            f"<figcaption>{name}<br>{values[i]:.4g}</figcaption></figure>"
        )
    return f"<h3>{html.escape(metric)}: {label}</h3><div class=grid>{''.join(cards)}</div>"


def main(samplesheet, tsv_dir, jpg_dir, out_dir):
    with open(samplesheet, newline="") as f:
        sheet = list(csv.DictReader(f))
    labels = {r["name"]: r.get("stain_label") or "" for r in sheet}

    found = {}
    columns = []
    for path in sorted(glob.glob(os.path.join(tsv_dir, "*.tsv"))):
        with open(path, newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                found[row["name"]] = row
                columns.extend(c for c in row if c not in columns)

    failed = [n for n in labels if n not in found]
    rows = [found[n] for n in labels if n in found]
    if not rows:
        sys.exit("no slide produced a result")

    table = {m: np.array([number(r.get(m)) for r in rows]) for m, _ in METRICS}
    faint = {m: faint_scores(table[m], d) for m, d in METRICS}

    os.makedirs(out_dir, exist_ok=True)
    extra = [f"faint_z_{m}" for m, _ in METRICS]
    fields = ["name", "status", "stain_label"] + extra + [c for c in columns if c != "name"]
    with open(os.path.join(out_dir, "histoqc_results.tsv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for i, r in enumerate(rows):
            z = {f"faint_z_{m}": f"{faint[m][i]:.3f}" for m, _ in METRICS}
            w.writerow({**r, **z, "status": "ok", "stain_label": labels[r["name"]]})
        for n in failed:
            w.writerow({"name": n, "status": "failed", "stain_label": labels[n]})

    lines = [
        f"slides: {len(labels)}",
        f"histoqc finished: {len(rows)}",
        f"histoqc failed: {len(failed)}",
        "",
        "metric: p1 p5 p25 p50 p75 p95 p99 | faint side beyond z 2, z 3 (robust z, all slides, not a threshold yet)",
    ]
    for m, _ in METRICS:
        v = table[m]
        p = " ".join(f"{x:.4g}" for x in np.nanpercentile(v, [1, 5, 25, 50, 75, 95, 99]))
        lines.append(f"{m}: {p} | {int(np.nansum(faint[m] > 2))}, {int(np.nansum(faint[m] > 3))}")
    text = "\n".join(lines) + "\n"
    with open(os.path.join(out_dir, "histoqc_summary.txt"), "w") as f:
        f.write(text)
    print(text, end="")

    fig, axes = plt.subplots(1, len(METRICS), figsize=(4 * len(METRICS), 3.2))
    for ax, (m, _) in zip(axes, METRICS):
        v = table[m][np.isfinite(table[m])]
        ax.hist(v, bins=60, color="#4c78a8")
        ax.set_title(m, fontsize=10)
        ax.set_ylabel("slides")
        ax.tick_params(labelsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "vibrancy_distributions.png"), dpi=150)

    thumbs = os.path.join(out_dir, "thumbs")
    os.makedirs(thumbs, exist_ok=True)
    for jpg in glob.glob(os.path.join(jpg_dir, "*.jpg")):
        shutil.copy(jpg, thumbs)

    sections = []
    for m, _ in METRICS:
        ok = np.where(np.isfinite(faint[m]))[0]
        by_faint = ok[np.argsort(-faint[m][ok])]
        sections.append(review_section(m, rows, table[m], f"{REVIEW_COUNT} most faint", by_faint[:REVIEW_COUNT]))
        sections.append(review_section(m, rows, table[m], f"{REVIEW_COUNT} least faint", by_faint[-REVIEW_COUNT:][::-1]))
    page = (
        "<!doctype html><meta charset=utf-8><title>HistoQC vibrancy review</title><style>"
        "body{font:14px sans-serif;margin:16px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}"
        "figure{margin:0}img{width:100%;height:auto;border:1px solid #ccc}figcaption{font-size:11px;overflow-wrap:anywhere}</style>"
        f"<h1>HistoQC vibrancy review</h1><pre>{html.escape(text)}</pre>"
        '<img src="vibrancy_distributions.png" alt="" style="max-width:100%">' + "".join(sections)
    )
    with open(os.path.join(out_dir, "vibrancy_review.html"), "w") as f:
        f.write(page)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit("usage: hqc_summary.py <samplesheet.csv> <tsv_dir> <jpg_dir> <output_dir>")
    main(*sys.argv[1:])
