#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

params.samplesheet     = null
params.outdir          = 'results'
params.limit           = -1
params.keep_masks      = false
params.timeout_seconds = 2400

process HISTOQC {
    tag "$name"
    publishDir "${params.outdir}/slides", mode: 'copy', enabled: params.keep_masks, pattern: "${name}_histoqc"

    input:
    tuple val(name), path(slide)

    output:
    path "${name}.tsv", emit: tsv
    path "${name}.jpg", emit: jpg, optional: true
    path "${name}_histoqc"

    script:
    """
    timeout ${params.timeout_seconds} run-histoqc "${slide}" qc --nprocesses ${task.cpus}
    hqc_row.py qc "${name}" .
    mv qc "${name}_histoqc"
    """
}

process HISTOQC_SUMMARY {
    publishDir params.outdir, mode: 'copy'

    input:
    path tsvs, stageAs: 'tsv/*'
    path jpgs, stageAs: 'jpg/*'
    path samplesheet

    output:
    path 'histoqc_results.tsv'
    path 'histoqc_summary.txt'
    path 'vibrancy_distributions.png'
    path 'vibrancy_review.html'
    path 'thumbs'

    script:
    """
    hqc_summary.py "${samplesheet}" tsv jpg .
    """
}

workflow {
    if (!params.samplesheet) {
        error "Please give --samplesheet"
    }
    rows = Channel.fromPath(params.samplesheet, checkIfExists: true)
        .splitCsv(header: true)
        .map { row -> tuple(row.name, file(row.Address)) }
    def limit = params.limit.toString().toInteger()
    slides = limit > 0 ? rows.take(limit) : rows

    HISTOQC(slides)
    HISTOQC_SUMMARY(
        HISTOQC.out.tsv.collect(),
        HISTOQC.out.jpg.collect().ifEmpty([]),
        file(params.samplesheet)
    )
}
