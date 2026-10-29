[TOC]

# ApiaceaeDB user guide

Editorial draft — 27 October 2026. Prepared for the genomic, transcriptomic, and predicted antimicrobial peptide scope of the manuscript. Metabolomics is excluded. Dataset coverage follows the author's stated collection of 34 species and their chromosome-level assemblies, spanning approximately 20 genera; expression and AMP coverage must be confirmed separately. This draft is not yet the guide served by the website.

> Before publication: replace the screenshot placeholders with images from the tested public release. Sections marked “pending validation” describe unfinished functions and must be updated or removed before publishing the guide.

## 1. Getting started

ApiaceaeDB provides species information, genome assembly summaries, searchable gene annotations, gene-expression profiles, and predicted antimicrobial peptide candidates. Use the top navigation bar to move between Species, Genome, Transcriptome, AMPs, Tools, Download, Help, and Contact. Navigation and screenshots should reflect the manuscript's scope.

The homepage summarizes dataset sizes and provides shortcuts to frequently used functions. A gene-expression record is one stored measurement, not one RNA-seq sample. Peptide candidates are computational predictions, not experimentally validated activities.

> **Screenshot UG01 — Homepage.** Insert a full-width screenshot showing navigation, database statistics, and analysis shortcuts. Mark the main entry points with numbered callouts.

## 2. Species information

1. Open **Species** in the navigation bar.
2. Select a scientific name.
3. Review the scientific, Chinese, and common names; genus; taxonomy identifier; distribution; chromosome number; genome size; gene count; and description where available.
4. Inspect the representative image and its attribution.

Missing values indicate information that is not recorded. Genome size is a sequence length and should be expressed in bp, Mb, or Gb; “GB” denotes a storage unit and should be corrected in the final interface.

> **Screenshot UG02 — Species page.** Show one representative species, its metadata, and image attribution.

## 3. Genome resources

### 3.1 Assembly overview

Open **Genome → Assembly** to view genome size, gene count, N50, and BUSCO completeness where available. The current table reports sequence lengths in base pairs. Consult the release metadata for whether N50 is contig N50 or scaffold N50 and for the BUSCO assessment type and lineage dataset.

> **Screenshot UG03 — Assembly overview.** Show the table headers and several representative assembly records.

### 3.2 Searching genes

1. Open **Genome → Gene**.
2. Select a species or multiple species. In the native multiple-selection field, use Ctrl on Windows or Command on macOS to select additional entries.
3. Enter a gene identifier or part of an identifier in **Gene Name**.
4. Optionally add Pfam, Swiss-Prot, GO, EC, or KO search criteria.
5. Select **Search** and inspect the results. Criteria in different fields are combined to narrow the search.
6. Select a gene identifier to open its detail page. Use **Reset** to clear the search.

Use the dedicated gene-search form for this workflow. The unfiltered page currently defaults to Anethum graveolens; it should not be interpreted as a family-wide inventory. Pagination and the navbar quick search require final validation.

> **Screenshot UG04 — Gene search.** Show selected species, an example query using a gene in the final release, and the resulting table.

### 3.3 Gene details and sequences

The detail page displays the selected gene's species, chromosome or scaffold, coordinates, strand, and available annotations. Follow annotation links to explore the corresponding reference database entries. Use **Copy** beside the CDS or protein sequence to copy the sequence text. Add a FASTA header before using copied sequence text in a tool that requires FASTA format.

Use the genome-browser link to inspect the surrounding genomic region. Gene identifiers should be interpreted together with their species and assembly; identical identifiers may occur in different assemblies.

> **Screenshot UG05 — Gene details.** Include the coordinate panel, annotation links, CDS/protein controls, and browser entry point.

## 4. Transcriptome resources

### 4.1 RNA-seq sample overview

Open **Transcriptome → RNASeq-Sample** to view the species, tissue, and replicate labels represented in the sample overview. The current implementation infers these combinations from expression records for one representative gene per species. It is not a complete accession-level sample catalogue and may omit combinations absent from that gene.

> **Screenshot UG06 — RNA-seq overview.** Show the species, tissue, and replicate columns. Do not label this image as a BioProject/SRR metadata catalogue.

### 4.2 Searching gene expression

1. Open **Transcriptome → Expression**.
2. Enter one or more gene IDs, separated by commas.
3. Select species, tissues, and replicates as required.
4. Optionally set minimum and maximum TPM values.
5. Select **Apply Filters**.

Select **Mean** to summarize the available replicates for each gene/species/tissue combination. In the present implementation, Mean takes precedence over selected individual replicate numbers and averages the records remaining after other filters. Applying expression thresholds before averaging changes which observations contribute to the mean.

The unfiltered page previews 100 records. Filtered webpage results are capped at 2,000 records; the displayed matching count can exceed the number available for browsing. Narrow the query to inspect a manageable subset. Matching filtered CSV exports are not subject to this display cap. An export from an unfiltered preview returns the preview data.

> **Screenshot UG07 — Expression search.** Show query fields, matching count, replicate selection, and table pagination.

### 4.3 Expression plots and correlations

Choose **Visualize → Bar Chart** or **Visualize → Heatmap** to plot the current table page. These charts do not automatically include all matching records. Restrict the query to one species to avoid ambiguity when gene or tissue labels recur.

Choose **Visualize → Correlation Heatmap** to request pairwise Pearson correlations between genes across tissue-level profiles. The calculation uses the retrieved records, subject to the 2,000-record cap, and averages observations sharing tissue and gene labels. Use a focused query within one species with multiple shared tissues. Constant profiles or insufficient overlapping measurements can yield undefined correlations. Correlation indicates association, not a demonstrated regulatory relationship.

The separate **Generate Heatmap** button currently uses a different request flag and needs correction before it can be documented as an equivalent route.

> **Screenshot UG08 — Expression visualization.** Reserve panels A–C for a bar chart, expression heatmap, and correlation heatmap. Include the selected species, genes, and tissues in the caption.

### 4.4 Downloading expression records

Use **Export All Data** to download matching filtered expression records as CSV. To use **Download Selection**, check the relevant table rows first. Selection is currently based on gene identifiers, so it may export additional matching tissue or replicate records for those genes rather than exactly the checked rows. Confirm export behavior in the final release.

> **Screenshot UG09 — Expression export.** Show the export controls and a small example of the downloaded CSV.

## 5. Predicted antimicrobial peptides

Open **AMPs** to inspect candidate peptides linked to source genes and species. Records contain an smORF ID, gene ID, species, peptide sequence, recorded start/end positions, and a prediction score.

1. Enter one or more gene IDs, separated by commas, or select species.
2. Optionally set minimum and maximum prediction scores.
3. Select **Search** and inspect the resulting candidates.
4. Use **Reset** to return to the initial preview.

Predictions were generated with locally retrained PlantAMP-based models and a study-specific inference script. The script averages 50 dropout-enabled predictions per fold and then averages five folds equally; its binary AMP threshold is 0.5. A stricter database-retention threshold, if used, must be documented separately. Higher scores do not establish experimentally confirmed antimicrobial activity or guarantee probability calibration.

The interface includes CSV export controls, but their JavaScript integration requires correction and testing before export instructions can be finalized. The unfiltered view previews 100 records; do not describe it as a full-database export. The coordinate reference and indexing convention for peptide positions also require confirmation before describing them as genomic, CDS, or protein coordinates.

> **Screenshot UG10 — AMP search.** Show the filters, candidate sequences, and score column. Add the confirmed database-retention threshold to the final caption.

## 6. Analysis tools

### 6.1 BLAST sequence similarity searches

1. Open **Tools → Blast**.
2. Choose the program appropriate to your input and target:

| Program | Query | Target database |
|---|---|---|
| BLASTN | Nucleotide | CDS nucleotide sequences |
| BLASTP | Protein | Protein sequences |
| BLASTX | Translated nucleotide | Protein sequences |
| TBLASTN | Protein | Translated CDS nucleotide sequences |

3. Select one species or **All Species**. The latter uses the prepared combined database; arbitrary multi-species combinations are not supported by the current form.
4. Set an E-value cutoff.
5. Paste FASTA sequences. File upload is provided in the interface but requires a backend form-binding fix before it can be documented as working. Use only one input method after that fix is validated.
6. Submit the query and inspect sequence identities, alignment lengths, mismatches, E-values, and bit scores.
7. Use the results download control to save the displayed table as CSV.

The form validates a maximum of 50 FASTA entries and a 5 MB upload limit. These are input limits, not a guarantee of completion time. Similarity hits alone do not establish orthology.

> **Screenshot UG11 — BLAST input.** Show program, database, E-value, and FASTA input.
>
> **Screenshot UG12 — BLAST output.** Show a representative hit table and CSV control.

### 6.2 External HMMER workflow

1. Open **Tools → HMMER (Pfam Search)**.
2. Choose gene-ID input to retrieve stored protein sequences, or paste protein sequence data.
3. Submit the input to prepare the sequence text.
4. Copy the resulting FASTA text and open the linked external HMMER service.
5. Submit the sequences to that service and interpret its output there.

ApiaceaeDB prepares the sequences; the current workflow does not run HMMER locally or display returned domain results within ApiaceaeDB. Confirm the external service's accepted input and limits when submitting a job.

> **Screenshot UG13 — HMMER handoff.** Reserve panel A for input and panel B for prepared FASTA and the external-service link.

### 6.3 JBrowse genome browser

1. Open **Tools → JBrowse**.
2. Search the species list and open the browser for the selected species.
3. Navigate to a chromosome or genomic interval using the browser controls.
4. Inspect the reference sequence and available gene-annotation tracks; zoom and pan to examine neighboring features.

You can also enter through the link on a gene-detail page. Only tracks configured for that assembly should be described as available. Variant, RNA-seq, and other omics tracks are not implied by the presence of the browser. Public deployment requires replacement of the current localhost browser links.

> **Screenshot UG14 — JBrowse species selection.** Show the browser entry table.
>
> **Screenshot UG15 — Genomic region.** Show a reference interval and gene-annotation track with the assembly and coordinates visible.

### 6.4 Annotation enrichment

1. Open **Tools → Enrichment**.
2. Select a species and analysis option.
3. Paste at least three gene IDs, separated by newlines or commas. The form accepts up to 3,000 entries.
4. Set an adjusted P-value cutoff and submit the list.
5. Inspect annotation IDs, adjusted P-values, overlapping gene counts, and contributing genes. Download the displayed results as CSV if needed.

Current interpretation: the three GO-labelled choices use the same stored GO annotations without namespace separation. The KEGG-labelled option tests KO annotation groups without an explicit KO-to-pathway mapping. Do not interpret these results as separately implemented GO namespace analyses or pathway-level enrichment. The current background consists of genes with annotations for the selected analysis. Bubble plots are not implemented.

> **Screenshot UG16 — Enrichment input.** Show the selected species, gene list, and cutoff.
>
> **Screenshot UG17 — Enrichment output.** Show the annotation table and export control. Final labels must match the tested analysis unit.

### 6.5 Primer Design — pending validation

The interface is intended to design primer pairs from the stored CDS of a selected gene using Primer3 through primer3-py. The following workflow is a documentation draft for the repaired tool, not confirmation that the current endpoint works.

1. Obtain an exact gene ID from **Genome → Gene** and verify that its detail page contains a CDS.
2. Open **Tools → Primer Design** and select **Gene ID** mode.
3. Enter the gene ID and set the supported product-size, melting-temperature, and GC-content limits.
4. Submit the job.
5. After validation, inspect each pair's forward and reverse sequences (5′–3′), predicted product size, melting temperatures, and GC content.
6. Use Excel export only after it has been repaired and verified.

The form currently defines initial product-size limits of 100–300 bp, Tm limits of 57–63 °C, and GC-content limits of 20–80%; the backend requests up to five pairs. These are intended defaults, not validated performance results. Form fields, template controls, result rendering, and export are inconsistent in the current code. Chromosome-fragment mode explicitly remains unimplemented, and FASTA upload is not supported by this tool.

The selected template is a CDS. Predicted amplicon lengths therefore apply to that template; genomic DNA products can differ where introns intervene. Genome-wide primer specificity is not assessed by the current implementation. Check specificity and experimentally validate primer pairs before use.

> **Screenshot UG18 — Primer input, reserved.** Insert after repair, showing a valid ApiaceaeDB gene and the supported parameter controls.
>
> **Screenshot UG19 — Primer output, reserved.** Insert after successful end-to-end testing, showing primer sequences, product sizes, Tm, and verified export behavior.

## 7. Downloading source files

Open **Download** and locate the organism of interest. Separate links are provided for genome FASTA, gene annotations, Helixer annotations, CDS, and predicted protein sequences. Organism-specific and combined archive routes are also present. Files and prepared archives must exist on the server; links alone do not establish availability. Helixer files should be described as available only for organisms with validated files.

Download expression data through its search interface. Predicted protein sequences are not experimental proteomics measurements.

> **Screenshot UG20 — Download page.** Show the file categories and one verified organism-specific bundle. Record release/version information in the final caption.

## 8. Help and contact

Open **Help** to consult the guide. Use **Contact** to submit a subject and message describing a question, issue, or suggestion. Name and email are optional; provide an email address if you would like a response. For reproducible issue reports, include the page name, species, relevant IDs, query parameters, and the observed behavior.

> **Screenshot UG21 — Help and Contact.** Reserve panels for the guide navigation and feedback form. Use fictional contact details in screenshots.

## 9. Troubleshooting and interpretation

| Observation | Suggested action |
|---|---|
| No gene matches | Verify the species, assembly, and exact identifier; remove additional annotation filters. |
| No expression records | Confirm that the gene/species/tissue combination has expression coverage. Genome coverage does not imply RNA-seq coverage. |
| A plot omits expected records | Page charts use the current table page; filtered webpage data are capped at 2,000 records. Narrow the query or export matching data. |
| Correlation is undefined | Use one species and several shared tissues; exclude constant or insufficiently observed profiles. |
| BLAST returns no hits | Verify query type and target database, then consider a less stringent E-value cutoff. |
| A file link fails | Report the organism and file category; the file or prepared archive may be absent. |
| AMP score is high | Treat the entry as a predicted candidate, not a validated antimicrobial peptide. |
| Primer Design fails | This endpoint requires repair and release validation; retain this section as a draft until completed. |

## 10. Citation and reproducibility

When using ApiaceaeDB, cite the database article when available and the original datasets and tools relevant to your analysis. Record the database access date, assembly and annotation identifiers, query settings, and downloaded filenames. For PlantAMP-based candidate selection, report the database-retention threshold and distinguish it from the inference script's 0.5 classification threshold.
