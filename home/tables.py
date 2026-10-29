import django_tables2 as tables
from django.utils.safestring import mark_safe
from .models import Metabolite, MetaboliteExpression, GeneExpression # Make sure models are imported

class ExpressionTable(tables.Table):
    # Matches your Metabolite style perfectly
    selection = tables.TemplateColumn(
        template_code='<input type="checkbox" class="row-select" data-id="{{ record.gene }}">',
        verbose_name=mark_safe('<input type="checkbox" id="select-all">'),
        orderable=False,
        attrs={
            'th': {'style': 'width:60px; text-align:center; vertical-align:middle;'},
            'td': {'style': 'width:60px; text-align:center; vertical-align:middle;'}
        }
    )
    gene = tables.Column(verbose_name="Gene ID")
    species = tables.Column(verbose_name="Species")
    tissue = tables.Column(verbose_name="Tissue")
    replicate = tables.Column(verbose_name="Replicate")
    value = tables.Column(verbose_name="Expression (TPM)")

    class Meta:
        template_name = "django_tables2/bootstrap5.html"
        attrs = {
            'class': 'table table-striped table-hover align-middle',
            'style': 'width:100%; table-layout:fixed;'
        }
        empty_text = "No matching expressions found…"
        orderable = False # Removes clickable sorting links to match Metabolite page


# 1. Profile Table (Updated with your requested fixes)
class MetaboliteTable(tables.Table):
    # Fix 1: Use mark_safe so the checkbox actually renders as an input element
    selection = tables.TemplateColumn(
        template_code='<input type="checkbox" class="row-select" data-id="{{ record.pk }}">',
        verbose_name=mark_safe('<input type="checkbox" id="select-all">'),
        orderable=False,
        attrs={
            'th': {'style': 'width:60px; text-align:center; vertical-align:middle;'},
            'td': {'style': 'width:60px; text-align:center; vertical-align:middle;'}
        }
    )
    
    # Fix 3: Render CAS as a hyperlink to Common Chemistry
    cas = tables.TemplateColumn(
        template_code='{% if record.cas %}<a href="https://commonchemistry.cas.org/detail?cas_rn={{ record.cas }}" target="_blank" class="text-success text-decoration-none">{{ record.cas }}</a>{% else %}-{% endif %}',
        verbose_name='CAS',
        attrs={'td': {'style': 'white-space:nowrap;'}}
    )
    
    # Fix 3: Render PubChem CID as a hyperlink to the official NCBI PubChem database
    pubchem_cid = tables.TemplateColumn(
        template_code='{% if record.pubchem_cid %}<a href="https://pubchem.ncbi.nlm.nih.gov/compound/{{ record.pubchem_cid }}" target="_blank" class="text-success text-decoration-none">{{ record.pubchem_cid }}</a>{% else %}-{% endif %}',
        verbose_name='PubChem CID',
        attrs={'td': {'style': 'white-space:nowrap;'}}
    )

    actions = tables.TemplateColumn(
        template_code='<a href="{% url \'home:metabolite_expression\' %}?metabolite__compounds={{ record.compounds }}" class="btn btn-sm btn-outline-success">View Abundance</a>',
        verbose_name='Actions',
        orderable=False,
        attrs={'td': {'style': 'width:140px; text-align:center; vertical-align:middle;'}}
    )

    class Meta:
        model = Metabolite
        fields = ('selection', 'compounds', 'class_1', 'class_2', 'rt', 'cas', 'pubchem_cid', 'smile', 'actions')
        attrs = {
            'class': 'table table-striped table-hover align-middle',
            'style': 'width:100%; table-layout:fixed;'
        }
        empty_text = "No matching metabolites found…"
        # Fix 2: Setting this to False removes the clickable sorting links from the headers
        orderable = False 


class MetaboliteExpressionTable(tables.Table):
    selection = tables.TemplateColumn(
        template_code='<input type="checkbox" class="row-select" data-id="{{ record.pk }}">',
        verbose_name=mark_safe('<input type="checkbox" id="select-all">'), # FIX: Checkbox renders properly
        orderable=False,
        attrs={
            'th': {'style': 'width:60px; text-align:center; vertical-align:middle;'},
            'td': {'style': 'width:60px; text-align:center; vertical-align:middle;'}
        }
    )
    compound = tables.Column(
        accessor='metabolite.compounds',
        verbose_name='Compound',
        attrs={'td': {'style': 'min-width:220px; max-width:260px; white-space:normal; word-wrap:break-word;'}}
    )
    species = tables.Column(
        accessor='species.name_latin',
        verbose_name='Species',
        attrs={'td': {'style': 'min-width:160px; white-space:nowrap;'}}
    )
    tissue = tables.Column(
        accessor='tissue.name',
        verbose_name='Tissue',
        attrs={'td': {'style': 'min-width:120px; white-space:nowrap;'}}
    )
    relative_amount = tables.Column(
        verbose_name='Abundance',
        attrs={
            # We add styling for BOTH the Header (th) and Data Cells (td)
            'th': {'style': 'text-align: center; vertical-align: middle; width: 120px;'},
            'td': {'style': 'text-align: center; vertical-align: middle; width: 120px;'}
        }
    )

    class Meta:
        model = MetaboliteExpression
        fields = ('selection', 'compound', 'species', 'tissue', 'relative_amount')
        attrs = {
            'class': 'table table-striped table-hover align-middle',
            'style': 'width:100%; table-layout:fixed;'
        }
        empty_text = "No matching expressions found…"
        orderable = False # FIX: Removes clickable headers
        

class AmpTable(tables.Table):
    # Safe checkbox column
    selection = tables.TemplateColumn(
        '<input type="checkbox" class="row-checkbox" value="{{ record.smorf }}">',
        orderable=False,
        verbose_name=mark_safe('<input type="checkbox" id="selectAll">')
    )
    
    smorf = tables.Column(verbose_name="smORF ID")
    gene = tables.Column(verbose_name="Gene ID")
    species = tables.Column(verbose_name="Species")
    prob = tables.Column(verbose_name="Probability")
    start = tables.Column(verbose_name="Start")
    end = tables.Column(verbose_name="End")
    seq = tables.Column(verbose_name="Sequence")

    class Meta:
        orderable = False # CRITICAL: Prevents DB crashes on load
        empty_text = "No antimicrobial peptides found matching your criteria."
        attrs = {
            "class": "table table-hover table-striped table-bordered text-center",
            "th": {"style": "text-align: center; vertical-align: middle;"},
            "td": {"style": "text-align: center; vertical-align: middle;"}
        }
        sequence = ('selection', 'smorf', 'gene', 'species', 'prob', 'start', 'end', 'seq')