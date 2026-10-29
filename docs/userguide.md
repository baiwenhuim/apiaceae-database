[TOC]

## Apiaceae Database User Guide

**Welcome to the Apiaceae Database**  
This multi-species genomic database provides a unified platform for exploring genomes, genes, annotations, and comparative genomics across medicinal plants of the Apiaceae family. By integrating high-confidence gene predictions, functional annotations (KO, EC, Pfam, NR, Swiss-Prot, GO), and conserved synteny information, this portal empowers researchers to **systematically investigate the genetic basis, evolutionary conservation, and molecular mechanisms of secondary metabolite biosynthesis**. Resources are tailored to support the identification of biosynthetic gene clusters, pathway reconstruction, cross-species pathway conservation and novelty analysis, and the discovery of enzymes and regulatory factors governing the accumulation of medicinally important specialized metabolites. 

The database integrates genome, transcriptome, and metabolome data from 30 Apiaceae species, including **11 newly assembled high-quality genomes** (Glehnia littoralis, Cnidium monnieri, Anethum graveolens, Pastinaca sativa, Conium maculatum, Carum carvi, Ferula sinkiangensis, Cicuta virosa, Oenanthe javanica, Changium smyrnioides, and Dickinsia hydrocotyloides) and **19 previously published genomes** (with references).  

It serves as a centralized platform to store, mine, analyze, integrate, and disseminate omics data across Apiaceae species. The database contains all publicly available genome and transcriptome profiles for the family, along with comprehensive sequence annotations (against Nr, UniProt, GO, KEGG, EC, Pfam, InterPro, eggNOG, etc.) and comparative genomics results (synteny blocks and homologous gene pairs).  

Using **genes** as the core unit, the platform links multidimensional omics data within species and enables cross-species comparisons via homologous gene relationships. A suite of user-friendly tools—including BLAST, Genome Browser, GO/KEGG Enrichment, Synteny Viewer, and Homolog Finder—facilitates data exploration and mining.  

**Figure 1.** [Database workflow](https://magen.whu.edu.cn/magendb/help/construction).

---

### 2. Navigation and Main Modules

Access the database via the top navigation bar: **Home | Species | Genome | Transcriptome | Metabolome | Antimicrobial Peptide | Tools | Download | Help**.

The **Home** page provides an introduction to the Apiaceae family, database statistics (number of species, genomes, transcriptomes, metabolites, etc.), and quick links to key resources.

#### 2.1 Species

Access species pages from the **Species** dropdown in the main navigation bar. Click any species name to view a dedicated page with:

- Scientific overview
- Geographical distribution and origin
- Chromosome number
- Key publications
- Other descriptive information

**Example**: For *Angelica sinensis*, the page displays Species Name, Family, Geographic Origin, Chromosome Number, and Publication details.

#### 2.2 Genome

##### 2.2.1 Assembly

The **Assembly** module summarizes high-quality genome assemblies. Currently, the database includes **33 chromosome-level assemblies** from various sources.

On the assembly page, you can view:

- **Basic statistics**: Genome size (bp), gene count, N50 value, BUSCO completeness (%).
- Clickable species names to jump to the corresponding species page.

##### 2.2.2 Gene

The **Gene** module provides detailed gene structures and functional annotations for each genome, derived from comprehensive pipelines using Nr, UniProt, InterPro, Pfam, eggNOG-mapper, and other databases.

**Search options** include genome version, chromosome coordinates, gene name/ID, and functional keywords.

Clicking a gene link opens a detailed card with the following tabs/sections:

- **Basic Information**: Genomic position, length, synonyms, functional description, GO terms, KEGG pathways.
- **Sequences**: Nucleic acid (CDS/genomic) and protein sequences (copy or send directly to BLAST).
- **Homologs**: Orthology diagram and list of homologous genes across other Apiaceae genomes.
- **Variants**: List of SNPs/InDels affecting the gene (if available).
- **Expression**: Expression levels (TPM/FPKM) across samples and projects; significantly differentially expressed genes are highlighted with project comparisons.
- **Visualization**: Embedded **Genome Browser** view of the gene locus and surrounding region.

#### 2.3 Transcriptome

##### 2.3.1 RNA-Seq Samples

The **RNA-Seq Sample** section lists metadata for all collected RNA-Seq samples, including detailed sample descriptions, experimental conditions, tissues, and overall alignment statistics.

##### 2.3.2 Expression Profiles

Using standardized pipelines, the **Expression** module provides transcriptome profiles for **31 Apiaceae species** across diverse tissues and experimental conditions.

**Search** by gene ID, species, or tissue. For each dataset/project:

- **Visualization**: Interactive charts (e.g., bar or line plots) of TPM values across samples. Select genes via dropdown.
- **Differential Expression**: Pre-computed up- and down-regulated gene lists between experimental conditions (based on sample grouping by metadata).

#### 2.4 Metabolome

The **Metabolome** module offers powerful, flexible access to metabolite profiles across species and tissues.

**Advanced Search Panel** (top section, collapsible on mobile):

- **Quick Search bar** (prominent, with autocomplete): Search by metabolite name, ID, or keyword → instantly filters the table below.
- **Filter Modes** (expandable cards/tabs):
  - By Metabolite → all expression records across species/tissues
  - By Species → all metabolites × all tissues
  - By Tissue → all metabolites × all species
- **Advanced Query Builder** (expandable): Build complex AND/OR conditions (e.g., Species = *Daucus carota* AND Tissue = Root AND Expression > 5 μmol/g) using multi-select dropdowns and numeric range sliders.
- **Search** and **Reset** buttons.

**Results Table**:

- **Default view** (on page load): All metabolites with columns such as Metabolite ID, Name, Molecular Formula, CAS Number, and number of available expression records.
- **After search/filter**: Switches to expression-level results with columns: Metabolite | Species | Tissue | Expression Value | Unit | Fold-change (vs. control) | p-value | Source/Project.

**Table features**:

- Pagination (20/50/100 rows per page) + “Show all” option for small result sets.
- Clickable column headers for sorting + free-text filter per column.
- Checkboxes for bulk actions (Export selected, Visualize selected).
- Responsive design: collapses to cards on mobile.
- Loading indicator + “X results found in Y seconds” message.

**Visualization Bar** (sticky, appears with results):

- Dropdown options: Bar chart, Heatmap, Volcano plot (fold-change), Line profile (across tissues).
- Opens in a modal with interactive Plotly charts.
- Modal export options: PNG/PDF/SVG images + raw data (CSV/Excel) + “Add to report”.

**Click Behaviors**:

- **Metabolite Name/ID** → Opens a detailed metabolite card (new tab or modal) showing chemical structure (RDKit-rendered), properties, full expression table (with mini-heatmaps), literature references, and linked pathways.
- **Expression row** → Opens the same modal, pre-filtered to that record.

**Additional Professional Features**:

- **Permanent Sidebar Filters** (left panel, ~250px): Multi-select for Species and Tissues (with internal search), expression range slider, data source filter.
- **Saved Searches & Favorites**: Heart icon on rows; access “My Collections” from the top bar.
- **Export Options**: Top-right button to download current table or all filtered data (CSV, Excel, JSON).
- **Accessibility & Performance**: Keyboard shortcuts (press `/` to focus search), ARIA labels, server-side pagination, progress indicators.
- **Optional Enhancements**: Dark mode toggle, “Compare metabolites” (select 2–5 for side-by-side heatmaps), tooltips explaining units/methods on column headers.

#### 2.5 Antimicrobial Peptide

The **Antimicrobial Peptide** module lists predicted AMPs from small open reading frames (smORFs). Each entry includes:

- Peptide sequence
- Start/end position in the parent gene
- AMP prediction score (probability)
- Classification (AMP or non-AMP), with high-confidence entries having probability > 0.9

---

### 3. Tools

#### 3.1 BLAST

The BLAST tool supports searches against genome, CDS, and protein sequence databases for up to 31 species. Users can select single or multiple species and submit query sequences for similarity searches (BLASTN, BLASTP, etc.) or pairwise alignment.

#### 3.2 Genome Browser

The **Genome Browser** (powered by JBrowse) enables interactive visualization of genome sequences, gene structures, tracks for SNPs, InDels, and other features. Users can export images of selected regions.

**Implementation note** (for developers): To embed JBrowse Linear Genome View, include the required sources and React dependencies, then render the component with your configured assemblies and tracks.

#### 3.3 GO/KEGG Enrichment

**GO Enrichment**:

1. Select target species, input a gene set (list of IDs), set p-value and q-value thresholds, and submit (processing ~1 minute).
2. Results include an interactive **bubble plot** (bubble size = number of genes; color intensity = corrected p-value, redder = more significant).
3. Download the plot (image) or full results table (sortable, Excel export).

**KEGG Enrichment** follows the same workflow and output format, with pathway-focused bubble plots.

#### 3.4 Synteny Viewer

Synteny analysis was performed using MUMmer on whole-genome sequences of 15 species (including intra- and inter-species comparisons).

**Usage**:

1. Select target species/genome versions and click **View**.
2. In the **dot plot**, select a region of interest and open the **linear synteny view**.
3. Use the **track selector** to overlay GFF annotation tracks for gene-level details in collinear regions.

---

### 4. Download, Contact & Help

The **Download** section provides direct access to all publicly released data, including:

- 30 genome sequences and their annotations
- Genome-wide variation data (for 9 species)
- Transcriptome profiling results (for 13 species)
- Germplasm information (for 15 species)

Data still under embargo before publication is not yet available for download.

For questions, bug reports, or collaboration, use the **Contact** form or email provided on the **Help** page. The Help section also includes FAQs, tutorials, and data citation guidelines.
