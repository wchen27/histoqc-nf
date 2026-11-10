# histoqc-nf

Nextflow workflow that runs HistoQC on each slide and summarises the measures used to look for faint slides.

- Container: `wchen27/histoqc-cpu:2.0-f35e518`, config `v2.1`, 1 CPU and 8 GB per slide, retried once with double memory
- Input: `--samplesheet` csv with `name` and `Address`, `stain_label` is optional
- `--limit N` runs the first N slides, `--keep_masks true` also publishes each slide's HistoQC folder
- A slide that fails twice is skipped and listed as `failed`

Output in `results/`:
- `histoqc_results.tsv`: every HistoQC metric per slide, plus a robust z-score towards faint for each candidate measure
- `histoqc_summary.txt`: counts and percentiles
- `vibrancy_distributions.png`: histogram of each candidate measure
- `vibrancy_review.html` and `thumbs/`: the most and least faint slides for each measure

No participant data is stored in this repository. The samplesheet and outputs stay in the research environment.
