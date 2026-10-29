from django import forms
from django.core.exceptions import ValidationError
import pandas as pd
from .models import Species, Tissue


class PrimerDesignForm(forms.Form):
    SEARCH_TYPES = [
        ('gene', 'Gene ID'),
        ('fragment', 'Chromosome Fragment'),
    ]
    
    search_type = forms.ChoiceField(
        choices=SEARCH_TYPES,
        label="Search Type",
        widget=forms.RadioSelect,
        initial='gene'
    )
    
    # Gene mode
    gene_id = forms.CharField(
        label="Gene ID",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Agr10G0001-RA'})
    )
    
    # Fragment mode
    chr = forms.CharField(
        label="Chromosome",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. chr10'})
    )
    start = forms.IntegerField(
        label="Start",
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'start position'})
    )
    end = forms.IntegerField(
        label="End",
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'end position'})
    )

    # Primer3 Parameters
    primer_product_size_min = forms.IntegerField(
        label="Product Size Min", initial=100, required=False
    )
    primer_product_size_max = forms.IntegerField(
        label="Product Size Max", initial=300, required=False
    )
    primer_tm_min = forms.FloatField(
        label="Tm Min", initial=57.0, required=False
    )
    primer_tm_max = forms.FloatField(
        label="Tm Max", initial=63.0, required=False
    )
    primer_gc_min = forms.FloatField(
        label="GC% Min", initial=20.0, required=False
    )
    primer_gc_max = forms.FloatField(
        label="GC% Max", initial=80.0, required=False
    )


class EnrichmentForm(forms.Form):
    DATABASE_CHOICES = [
        ('GO_BP', 'GO: Biological Process'),
        ('GO_MF', 'GO: Molecular Function'),
        ('GO_CC', 'GO: Cellular Component'),
        ('KEGG', 'KEGG Pathways'),
    ]

    analysis_type = forms.ChoiceField(
        choices=DATABASE_CHOICES, 
        initial='GO_BP',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # We will populate this dynamically in __init__ just like the BLAST form!
    species = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'class': 'form-select'}))
    
    pvalue_cutoff = forms.FloatField(
        initial=0.05, 
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'max': '1.0', 'min': '0.0'})
    )
    
    SAMPLE_GENES = "Agi3G4375-RA\nAgi6G5049-RA\nAgi3G4141-RA\nAgi10G3095-RA"
    
    gene_list = forms.CharField(
        required=True, 
        initial=SAMPLE_GENES,
        widget=forms.Textarea(attrs={'class': 'form-control text-monospace', 'rows': 8, 'placeholder': 'Paste one Gene ID per line...'}),
        label="Paste Gene IDs"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically load species just like the BLAST tool
        sp_choices = []
        try:
            for sp in Species.objects.all().order_by('name_latin'):
                sp_choices.append((sp.name_latin.lower().replace(' ', '_'), sp.name_latin))
        except Exception:
            pass
        self.fields['species'].choices = sp_choices
        if sp_choices:
            self.fields['species'].initial = sp_choices[0][0] # Default to the first species
            
    def clean_gene_list(self):
        # Clean up the pasted text: split by lines, remove empty lines and extra spaces
        raw_genes = self.cleaned_data['gene_list']
        gene_list = [g.strip() for g in raw_genes.replace(',', '\n').split('\n') if g.strip()]
        
        if len(gene_list) < 3:
            raise ValidationError("Please provide at least 3 valid Gene IDs for meaningful enrichment analysis.")
        if len(gene_list) > 3000:
            raise ValidationError("Maximum limit is 3000 genes per analysis to prevent server overload.")
            
        return gene_list

        
class BlastForm(forms.Form):
    PROGRAM_CHOICES = [
        ('blastn', 'BLASTN (Nucleotide to Nucleotide)'),
        ('blastp', 'BLASTP (Protein to Protein)'),
        ('blastx', 'BLASTX (Nucleotide to Protein)'),
        ('tblastn', 'TBLASTN (Protein to Nucleotide)'),
    ]

    # 1. Set default program to 'blastp'
    program = forms.ChoiceField(
        choices=PROGRAM_CHOICES, 
        initial='blastp', 
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    database = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'class': 'form-select'}))
    
    evalue = forms.FloatField(initial=1e-5, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1e-5'}))
    
    # 2. Add the default sample sequence
    SAMPLE_FASTA = ">test_seq_1\nMASSKIVLFAVLLAGVDPQIRGKKAVTKQKKDGKRKRSRKEYSYVYKVLKQHPDSGNSKAMGIMNSFVNDIFERIAGEASRLGHYNKRSTITRSEIQLAVRLLLPGELSKHAVSEGSKAVTKYTSSKG"
    
    sequence_text = forms.CharField(
        required=False, 
        initial=SAMPLE_FASTA,
        widget=forms.Textarea(attrs={'class': 'form-control text-monospace', 'rows': 6}),
        label="Paste FASTA Sequence(s)"
    )
    
    sequence_file = forms.FileField(
        required=False, 
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.fasta,.fa,.txt'}),
        label="Or Upload FASTA File"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        db_choices = [('all_species', 'All Species')]
        
        try:
            for sp in Species.objects.all().order_by('name_latin'):
                db_file_name = sp.name_latin.lower().replace(' ', '_')
                db_choices.append((db_file_name, sp.name_latin))
        except Exception:
            pass 
            
        self.fields['database'].choices = db_choices
        
        # 3. Set the default database to Daucus carota
        self.fields['database'].initial = 'daucus_carota'

    def clean(self):
        # ... (keep your existing clean method exactly the same) ...
        cleaned_data = super().clean()
        seq_text = cleaned_data.get("sequence_text")
        seq_file = cleaned_data.get("sequence_file")

        if not seq_text and not seq_file:
            raise ValidationError("Please either paste a sequence or upload a file.")
        if seq_text and seq_file:
            raise ValidationError("Please use ONLY ONE method: either paste a sequence OR upload a file, not both.")

        if seq_file:
            if seq_file.size > 5 * 1024 * 1024:
                raise ValidationError("File is too large. Maximum size is 5 MB.")
                
        fasta_content = ""
        if seq_text:
            fasta_content = seq_text
        elif seq_file:
            fasta_content = seq_file.read().decode('utf-8')
            seq_file.seek(0)

        sequence_count = fasta_content.count('>')
        
        if sequence_count > 50:
            raise ValidationError(f"Too many sequences! You provided {sequence_count}, but the maximum allowed is 50.")
        if sequence_count == 0:
            raise ValidationError("Invalid FASTA format. Sequences must start with a '>' character.")

        return cleaned_data


class ExpressionSearchForm(forms.Form):
    # Text input allows multiple comma-separated genes (e.g., "GeneA, GeneB") without crashing the browser
    gene_id = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Gene1, Gene2'}),
        label="Gene ID(s)"
    )
    
    # ModelMultipleChoiceField allows selecting multiple species
    species = forms.ModelMultipleChoiceField(
        queryset=Species.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '4'}),
        label="Species"
    )
    
    # ModelMultipleChoiceField allows selecting multiple tissues
    tissue = forms.ModelMultipleChoiceField(
        queryset=Tissue.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '4'}),
        label="Tissue"
    )
    
    REPLICATE_CHOICES = [
        ('1', '1'), ('2', '2'), ('3', '3'), ('mean', 'Mean')
    ]
    # MultipleChoiceField allows selecting multiple replicates
    replicate = forms.MultipleChoiceField(
        choices=REPLICATE_CHOICES,
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '4'}),
        label="Replicate"
    )
    min_expression = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min', 'step': '0.01'}),
        label="Min Expression (TPM)"
    )
    
    max_expression = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max', 'step': '0.01'}),
        label="Max Expression (TPM)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # FIX: Use self.fields instead of self.form.fields
        if 'species' in self.fields:
            self.fields['species'].label_from_instance = lambda obj: obj.name_latin


class AmpSearchForm(forms.Form):
    gene_id = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. GeneA, GeneB'}),
        label="Gene ID(s)"
    )
    
    species = forms.ModelMultipleChoiceField(
        queryset=Species.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '4'}),
        label="Species"
    )
    
    min_probability = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min', 'step': '0.01'}),
        label="Min Probability"
    )

    max_probability = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max', 'step': '0.01'}),
        label="Max Probability"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Safely override the label to show Latin name
        if 'species' in self.fields:
            self.fields['species'].label_from_instance = lambda obj: obj.name_latin


from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'John Doe'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'johndoe@example.com'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Issue or Suggestion', 'required': True}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Please detail your feedback here...', 'required': True}),
        }