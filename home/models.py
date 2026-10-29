from django.db import models

# --------------------------
# Core Models (Normalized Design)
# --------------------------
class Species(models.Model):
    """Master table for all Apiaceae species (avoids duplicate species names)"""
    # use Taxonomy_ID as unique code to represent species, which are numbers less than 8 digits
    taxonomy_id = models.PositiveIntegerField(unique=True, verbose_name="Taxonomy ID")
    name_cn = models.CharField(max_length=50, verbose_name="Chinese Name")  # e.g., 莳萝
    name_latin = models.CharField(max_length=100, blank=True, verbose_name="Latin Name")  # e.g., Anethum graveolens
    name_eng = models.CharField(max_length=100, blank=True, verbose_name="English Name")
    description = models.TextField(blank=True, verbose_name="Description")
    genus = models.CharField(max_length=50, blank=True, verbose_name="Genus")  # 属，e.g., Anethum
    n50 = models.BigIntegerField(blank=True, null=True, verbose_name="N50 (bp)")
    busco = models.DecimalField(
        max_digits=5, decimal_places=2,
        blank=True, null=True,
        verbose_name="BUSCO (%)"
    )
    genome_size_bp = models.BigIntegerField(blank=True, null=True, verbose_name="Genome Size (bp)")
    genome_size = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Genome Size (GB)")  # 基因组大小，保留2位小数，GB单位
    gene_count = models.IntegerField(blank=True, null=True, verbose_name="Gene Count")  # 基因总数
    chromosome_number = models.CharField(max_length=20, blank=True, verbose_name="Chromosome Number")  # 染色体数，e.g., 2n=18（用CharField兼容非纯数字格式）
    geographical_distribution = models.TextField(blank=True, verbose_name="Geographical Distribution")  # 地理分布
    species_pic_path = models.CharField(max_length=255, blank=True, verbose_name="Species Picture Path")  # 物种图片静态路径，e.g., 'static/home/species/shiluo.jpg'
    image_copyright = models.CharField(max_length=255, blank=True, verbose_name="Image Copyright")

    class Meta:
        db_table = 'species'
        verbose_name = "Species"
        verbose_name_plural = "Species"

    @property
    def browser_name(self):
        return self.name_latin.replace(" ", "_")

    def __str__(self):
        return f"{self.name_cn} (Taxonomy ID: {self.taxonomy_id})"

# Species relaed paper table
class SpeciesPaper(models.Model):
    """Related papers for each species (one species → multiple papers)"""
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="papers", verbose_name="Species")
    title = models.CharField(max_length=255, verbose_name="Paper Title")
    authors = models.CharField(max_length=500, blank=True, verbose_name="Authors")
    doi = models.CharField(max_length=100, blank=True, verbose_name="DOI")
    journal = models.CharField(max_length=100, blank=True, verbose_name="Journal")
    publish_date = models.DateField(blank=True, null=True, verbose_name="Publish Date")  # 日期类型，方便后续筛选

    class Meta:
        db_table = 'species_paper'
        verbose_name = "Species Paper"
        verbose_name_plural = "Species Papers"

    def __str__(self):
        return f"{self.title} ({self.journal}, {self.publish_date.year if self.publish_date else 'Unknown'})"

class Tissue(models.Model):
    """Master table for tissue types (standardizes tissue names across species)"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Tissue Name")  # e.g., 'root', 'young_leaf'
    description = models.TextField(blank=True, verbose_name="Tissue Description")

    class Meta:
        db_table = 'tissue'
        verbose_name = "Tissue"
        verbose_name_plural = "Tissues"

    def __str__(self):
        return self.name


class Gene(models.Model):
    """Gene metadata (single table for all species)"""
    # add index（species+chr、gene_id)
    gene_id = models.CharField(max_length=100, verbose_name="Gene ID")
    # 外键关联更新：从原来的 species.code 变为 species.taxonomy_id
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="genes", verbose_name="Species")
    chr = models.CharField(max_length=30, verbose_name="Chromosome/Scaffold")
    start = models.IntegerField(verbose_name="Start Position")
    end = models.IntegerField(verbose_name="End Position")
    strand = models.CharField(max_length=2, verbose_name="Strand (+/-)")  # Fixed typo: 'stand' → 'strand'
    pfam = models.CharField(max_length=200, blank=True, verbose_name="Pfam Domain")
    nr = models.CharField(max_length=50, blank=True, verbose_name="NCBI NR ID")
    swissprot = models.CharField(max_length=50, blank=True, verbose_name="SwissProt ID")
    go = models.TextField(blank=True)
    ec = models.CharField(max_length=1000, blank=True, verbose_name="EC Number")
    ko = models.CharField(max_length=1000, blank=True, verbose_name="KO ID")
    clean_ec = models.CharField(max_length=300, blank=True, verbose_name="Clean EC Predictions")
    cds = models.TextField(blank=True, verbose_name="CDS Sequence")        
    protein = models.TextField(blank=True, verbose_name="Protein Sequence")
    class Meta:
        db_table = 'gene'
        verbose_name = "Gene"
        verbose_name_plural = "Genes"
        unique_together = ('gene_id', 'species')  # Prevent duplicate gene IDs per species
        indexes = [
            models.Index(fields=['gene_id']),  # 按基因ID搜索
            models.Index(fields=['species', 'chr']),  # 按物种+染色体搜索（高频查询）
        ]

    def __str__(self):
        return f"{self.gene_id} ({self.species.name_cn}, {self.chr}:{self.start}-{self.end})"

class GeneExpression(models.Model):
    """Unified expression table (supports all species/tissues/replicates)"""
    # 关联链：GeneExpression → Gene → Species，可通过`gene.species`获取物种信息，无需直接存储
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE, related_name="expressions", verbose_name="Gene")
    tissue = models.ForeignKey(Tissue, on_delete=models.CASCADE, verbose_name="Tissue")
    replicate = models.IntegerField(default=1, verbose_name="Replicate Number")  # For technical/biological replicates
    expression_value = models.FloatField(null=True, blank=True, verbose_name="Expression Value (FPKM/TPM)")

    class Meta:
        db_table = 'gene_expression'
        verbose_name = "Gene Expression"
        verbose_name_plural = "Gene Expressions"
        unique_together = ('gene', 'tissue', 'replicate')  # Prevent duplicate entries
        indexes = [
            models.Index(fields=['gene']),  # 按基因查询表达量
            models.Index(fields=['tissue']),  # 按组织查询表达量
            # composite index for lighting-fast combined searches
            models.Index(fields=['gene', 'tissue', 'replicate']),
        ]

    def __str__(self):
        return f"{self.gene.gene_id} - {self.tissue.name} (Rep{self.replicate}): {self.expression_value}"


# ------------------------------
# Metabolite Basic Information
# ------------------------------
class Metabolite(models.Model):
    id = models.BigAutoField(primary_key=True, verbose_name="Metabolite ID")

    # compounds = models.TextField(unique=True, verbose_name="Compound")
    compounds = models.CharField(max_length=255, unique=True, verbose_name="Compound")
    cn_name = models.CharField(max_length=255, blank=True, verbose_name="Chinese Name")
    class_1 = models.CharField(max_length=100, blank=True, verbose_name="Major Class")
    class_2 = models.CharField(max_length=100, blank=True, verbose_name="Sub Class")
    formula = models.CharField(max_length=50, blank=True, verbose_name="Formula")
    molecular_weight = models.FloatField(null=True, blank=True, verbose_name="MW")
    rt = models.FloatField(null=True, blank=True, verbose_name="RT")
    score = models.FloatField(null=True, blank=True, verbose_name="Score")
    cas = models.CharField(max_length=50, blank=True, verbose_name="CAS")
    pubchem_cid = models.CharField(max_length=50, blank=True, verbose_name="PubChem CID")
    smile = models.TextField(blank=True, verbose_name="SMILE")

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "metabolite"
        indexes = [
            models.Index(fields=["compounds"]),
            models.Index(fields=["cn_name"]),
            models.Index(fields=["cas"]),
            models.Index(fields=["class_1", "class_2"]),
        ]

    def __str__(self):
        return self.cn_name or self.compounds[:50]


# ------------------------------
# Metabolite Expression
# ------------------------------
class MetaboliteExpression(models.Model):

    metabolite = models.ForeignKey(
        Metabolite, on_delete=models.CASCADE, related_name="expressions"
    )

    species = models.ForeignKey(
        Species, on_delete=models.CASCADE, related_name="metabolite_expressions"
    )

    tissue = models.ForeignKey(
        Tissue, on_delete=models.CASCADE, related_name="metabolite_expressions"
    )

    relative_amount = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "metabolite_expression"
        unique_together = ("metabolite", "species", "tissue")
        indexes = [
            models.Index(fields=["species", "tissue"]),
            models.Index(fields=["metabolite"]),
        ]

    def __str__(self):
        return f"{self.metabolite.compounds} | {self.species.name_latin} | {self.tissue.name}"


# ------------------------------
# Antimicrobial Peptide (AMP)
# ------------------------------
class AntimicrobialPeptide(models.Model):
    """Predicted antimicrobial peptides from smORFs"""

    smorf_id = models.CharField(max_length=150, unique=True, verbose_name="smORF ID")

    gene = models.ForeignKey(
        Gene,
        on_delete=models.CASCADE,
        related_name="amps",
        verbose_name="Gene"
    )

    sequence = models.TextField(verbose_name="Peptide Sequence")

    start_pos = models.IntegerField(verbose_name="Start Position")
    end_pos = models.IntegerField(verbose_name="End Position")

    amp_probability = models.FloatField(verbose_name="AMP Probability")

    prediction = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Prediction (AMP / non-AMP)"
    )

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "antimicrobial_peptide"
        verbose_name = "Antimicrobial Peptide"
        verbose_name_plural = "Antimicrobial Peptides"

        indexes = [
            models.Index(fields=["gene"]),
            models.Index(fields=["amp_probability"]),
        ]

    def __str__(self):
        return f"{self.smorf_id} ({self.gene.gene_id})"


class Feedback(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True, help_text="Optional")
    email = models.EmailField(blank=True, null=True, help_text="Optional, if they want a reply")
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Feedback" # Keeps it from saying "Feedbacks" in Admin

    def __str__(self):
        return f"{self.subject} - {self.created_at.strftime('%Y-%m-%d')}"