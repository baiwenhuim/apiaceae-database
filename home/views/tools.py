import os
import subprocess
import tempfile
from django.shortcuts import render
from django.conf import settings
from home.forms import BlastForm
from django.views import View
import re
import gseapy as gp
import pandas as pd
from django.shortcuts import render
from home.forms import EnrichmentForm, PrimerDesignForm
from home.models import Gene, Species  # Make sure to import your models

class PrimerDesignView(View):
    template_name = 'home/tools/primer_design.html'

    def get(self, request):
        form = PrimerDesignForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PrimerDesignForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            seq = None
            task = None

            # --------------------------
            # 1. Get sequence from Gene ID
            # --------------------------
            if data['search_type'] == 'gene':
                gene_id = data.get('gene_id')
                try:
                    gene = Gene.objects.get(gene_id=gene_id)
                    seq = gene.cds
                    task = f"Gene: {gene_id}"
                except Gene.DoesNotExist:
                    return render(request, self.template_name, {
                        'form': form, 'error': "Gene ID not found"
                    })

            # --------------------------
            # 2. Get sequence from Fragment (you need genome sequence API)
            # --------------------------
            elif data['search_type'] == 'fragment':
                return render(request, self.template_name, {
                    'form': form, 'error': "Fragment mode coming soon"
                })

            # --------------------------
            # 3. Run Primer3
            # --------------------------
            if seq and len(seq) > 50:
                primers = self.run_primer3(seq, data)
                return render(request, self.template_name, {
                    'form': form,
                    'primers': primers,
                    'task': task,
                    'sequence': seq
                })
            else:
                return render(request, self.template_name, {
                    'form': form, 'error': "Sequence too short or invalid"
                })
        return render(request, self.template_name, {'form': form})

    def run_primer3(self, seq, params):
        """Run primer3-py"""
        return primer3.bindings.design_primers(
            seq_args={
                'SEQUENCE_TEMPLATE': seq,
            },
            global_args={
                'PRIMER_PRODUCT_SIZE_RANGE': [
                    params['primer_product_size_min'],
                    params['primer_product_size_max']
                ],
                'PRIMER_MIN_TM': params['primer_tm_min'],
                'PRIMER_MAX_TM': params['primer_tm_max'],
                'PRIMER_MIN_GC': params['primer_gc_min'],
                'PRIMER_MAX_GC': params['primer_gc_max'],
                'PRIMER_NUM_RETURN': 5,
            }
        )

# --------------------------
# Excel Export
# --------------------------
def export_primers_excel(request):
    primers = request.session.get('primer_data')
    if not primers:
        return HttpResponse("No primer data")

    rows = []
    for i in range(primers.get('PRIMER_NUM_RETURN', 0)):
        rows.append({
            'Rank': i+1,
            'Left Primer': primers.get(f'PRIMER_LEFT_{i}_SEQUENCE'),
            'Right Primer': primers.get(f'PRIMER_RIGHT_{i}_SEQUENCE'),
            'Product Size': primers.get(f'PRIMER_PAIR_{i}_PRODUCT_SIZE'),
            'Left TM': primers.get(f'PRIMER_LEFT_{i}_TM'),
            'Right TM': primers.get(f'PRIMER_RIGHT_{i}_TM'),
            'Left GC': primers.get(f'PRIMER_LEFT_{i}_GC_PERCENT'),
            'Right GC': primers.get(f'PRIMER_RIGHT_{i}_GC_PERCENT'),
        })

    df = pd.DataFrame(rows)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="primers.xlsx"'
    df.to_excel(response, index=False)
    return response
    

def get_custom_gene_sets(species_form_val, analysis_type):
    """
    Streams gene annotations from the database to build the gseapy background dictionary.
    Optimized for low memory usage using .values_list() and .iterator().
    """
    gene_sets = {}
    background_genes = set()
    
    # Convert form value (e.g., 'daucus_carota') back to Latin name for querying
    target_species = species_form_val.replace('_', ' ')
    
    # 1. Query the database efficiently
    # We only fetch the exactly needed columns.
    gene_query = Gene.objects.filter(
        species__name_latin__iexact=target_species
    ).values_list('gene_id', 'go', 'ko').iterator(chunk_size=2000)
    
    # 2. Parse the text fields
    for gene_id, go_text, ko_text in gene_query:
        added_to_bg = False
        
        # Determine which field to parse based on user selection
        raw_terms = ""
        if analysis_type.startswith('GO') and go_text:
            raw_terms = go_text
        elif analysis_type == 'KEGG' and ko_text:
            raw_terms = ko_text
            
        if not raw_terms:
            continue
            
        # Split the terms robustly (handles commas, semicolons, and extra spaces)
        terms = [t.strip() for t in re.split(r'[,;]', raw_terms) if t.strip()]
        
        for term in terms:
            if term not in gene_sets:
                gene_sets[term] = []
            gene_sets[term].append(gene_id)
            added_to_bg = True
            
        if added_to_bg:
            background_genes.add(gene_id)
            
    return gene_sets, list(background_genes)


def enrichment_tool(request):
    results = []
    has_run = False
    error_msg = None

    if request.method == 'POST':
        form = EnrichmentForm(request.POST)
        if form.is_valid():
            user_genes = form.cleaned_data['gene_list']
            analysis_type = form.cleaned_data['analysis_type']
            species = form.cleaned_data['species']
            pvalue_cutoff = form.cleaned_data['pvalue_cutoff']

            has_run = True
            try:
                # 1. Fetch live database annotations
                custom_gene_sets, background_list = get_custom_gene_sets(species, analysis_type)
                
                if not custom_gene_sets:
                    raise ValueError(f"No background annotation data found for the selected species and database.")

                # 2. Run GSEAPY Local Enrichment
                enr = gp.enrich(
                    gene_list=user_genes,
                    gene_sets=custom_gene_sets,
                    background=background_list,
                    outdir=None,  # Keep in RAM
                    no_plot=True, # No hard drive writes
                    verbose=False
                )

                # 3. Process the Results
                if enr.results.empty:
                    error_msg = "No enriched terms found (data frame is empty)."
                else:
                    df = enr.results
                    # Filter by Adjusted P-value
                    df_filtered = df[df['Adjusted P-value'] <= pvalue_cutoff]

                    if df_filtered.empty:
                        error_msg = f"No terms found with an adjusted p-value <= {pvalue_cutoff}."
                    else:
                        for index, row in df_filtered.iterrows():
                            # Safely handle term splitting. 
                            # If database only has "GO:0001234" (no name), term_parts[1] won't break.
                            term_string = str(row['Term'])
                            if ' ' in term_string:
                                term_parts = term_string.split(' ', 1)
                                term_id = term_parts[0]
                                term_name = term_parts[1]
                            else:
                                term_id = term_string
                                term_name = "-"
                            
                            results.append({
                                'term_id': term_id,
                                'term_name': term_name,
                                'padj': f"{row['Adjusted P-value']:.4e}",
                                'gene_count': int(row['Overlap'].split('/')[0]),
                                'genes': row['Genes']
                            })

            except Exception as e:
                error_msg = f"Enrichment analysis failed: {str(e)}"
    else:
        form = EnrichmentForm()

    context = {
        'form': form,
        'results': results,
        'has_run': has_run,
        'error_msg': error_msg
    }
    return render(request, 'home/enrichment.html', context)


def blast_tool(request):
    form = BlastForm(request.POST or request.FILES or None)
    results = []
    error_msg = None

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        program = cd['program']
        db_name = cd['database']
        evalue = str(cd['evalue'])
        
        # Determine exactly which database folder to look in
        db_folder = 'nucleotide' if program in ['blastn', 'tblastn'] else 'protein'
        db_path = os.path.join(settings.BLAST_DB_DIR, db_folder, db_name)

        # Create a secure temporary file for the input sequence
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.fasta') as temp_fasta:
            if cd['sequence_text']:
                temp_fasta.write(cd['sequence_text'])
            else:
                temp_fasta.write(cd['sequence_file'].read().decode('utf-8'))
            temp_path = temp_fasta.name

        try:
            # Construct the BLAST command using Format 6 (Tabular)
            # Standard Format 6 columns: qacc sacc pident length mismatch gapopen qstart qend sstart send evalue bitscore
            blast_cmd = [
                program,
                '-query', temp_path,
                '-db', db_path,
                '-evalue', evalue,
                '-outfmt', '6',
                '-max_target_seqs', '50' # Limit hits per sequence to keep it fast
            ]

            # Run the command and capture the output
            process = subprocess.run(blast_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if process.returncode != 0:
                error_msg = f"BLAST Error: {process.stderr}"
            else:
                # Parse the Tabular Output
                for line in process.stdout.strip().split('\n'):
                    if line:
                        cols = line.split('\t')
                        
                        # 1. Catch the E-value and format it properly
                        raw_evalue = float(cols[10])
                        if raw_evalue == 0.0:
                            display_evalue = "0.0"
                        else:
                            # Force scientific notation with 2 decimal places (e.g., 4.14e-41)
                            display_evalue = f"{raw_evalue:.2e}" 

                        results.append({
                            'query': cols[0],
                            'subject': cols[1],
                            'identity': round(float(cols[2]), 2),  # Round to 2 decimal places for a cleaner look
                            'length': int(cols[3]),
                            'mismatches': int(cols[4]),
                            'evalue': display_evalue,              # Pass our clean string instead of the raw float
                            'bitscore': round(float(cols[11]), 1)  # Clean up the bitscore too
                        })

        except Exception as e:
            error_msg = f"Server Execution Error: {str(e)}"
        
        finally:
            # ALWAYS delete the temporary file, even if the command crashes
            if os.path.exists(temp_path):
                os.remove(temp_path)

    return render(request, 'home/blast.html', {
        'form': form,
        'results': results,
        'error_msg': error_msg,
        'has_run': request.method == 'POST'
    })



def hmmer_tool_page(request):
    """Renders the main HMMER tool input page."""
    return render(request, 'home/tools/hmmer_input.html')


def external_hmmer_redirect(request):
    sequence_data = ""
    
    if request.method == "POST":
        user_input = request.POST.get('input_data', '').strip()
        input_type = request.POST.get('input_type')

        if input_type == 'id':
            # Support multiple IDs (comma, space, or newline)
            gene_ids = re.split(r'[,\s\n]+', user_input)
            genes = Gene.objects.filter(gene_id__in=gene_ids)
            
            fasta_list = []
            for g in genes:
                if g.protein:
                    fasta_list.append(f">{g.gene_id}\n{g.protein}")
            sequence_data = "\n".join(fasta_list)
        else:
            sequence_data = user_input

    if not sequence_data:
        return render(request, 'home/tools/hmmer_input.html', {'error': 'No valid sequences found.'})

    return render(request, 'home/tools/hmmer_copy_go.html', {'sequence': sequence_data})