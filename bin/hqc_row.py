#!/usr/bin/env python3
import csv
import glob
import os
import sys

from PIL import Image


def read_results(path):
    with open(path, newline="", errors="replace") as f:
        lines = f.read().splitlines()
    header = None
    rows = []
    for line in lines:
        if line.startswith("#dataset:"):
            header = line[len("#dataset:"):].split("\t")
        elif line.strip() and not line.startswith("#") and header:
            rows.append(dict(zip(header, line.split("\t"))))
    return header, rows


def main(qc_dir, name, out_dir):
    results = os.path.join(qc_dir, "results.tsv")
    if not os.path.exists(results):
        sys.exit(f"no results.tsv for {name}")
    header, rows = read_results(results)
    if not rows:
        sys.exit(f"no result row for {name}")
    with open(os.path.join(out_dir, f"{name}.tsv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name"] + header, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerow({"name": name, **rows[0]})
    thumbs = [p for p in glob.glob(os.path.join(qc_dir, "*", "*_thumb.png")) if not p.endswith("_equalized_thumb.png")]
    if thumbs:
        image = Image.open(thumbs[0]).convert("RGB")
        image.thumbnail((500, 500))
        image.save(os.path.join(out_dir, f"{name}.jpg"), quality=85)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: hqc_row.py <qc_dir> <name> <output_dir>")
    main(*sys.argv[1:])
