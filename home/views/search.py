from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Avg # 用于多条件模糊查询
from django.http import HttpResponse
from django.contrib import messages

from ..models import Species, Gene, GeneExpression, Tissue
from ..forms import ExpressionSearchForm, AmpSearchForm
from ..models import Metabolite, MetaboliteExpression
from ..models import AntimicrobialPeptide
from django_tables2 import RequestConfig
from django_tables2.config import RequestConfig
from django_filters.views import FilterView
from ..tables import MetaboliteTable, MetaboliteExpressionTable
from home.tables import ExpressionTable, AmpTable
from ..filters import MetaboliteFilter, MetaboliteExpressionFilter
import csv
import plotly.express as px
import pandas as pd


# ========== Gene Search View ==========
def gene(request):
    # 1. Dynamic species list
    species_list = Species.objects.all().order_by('name_latin')
    species_choices = [(sp.taxonomy_id, f"{sp.name_latin} ({sp.name_cn})") for sp in species_list]

    # 2. Get list of multiple species IDs and REMOVE empty strings
    raw_species = request.GET.getlist('species')
    species_selected = [sp for sp in raw_species if sp.strip()] # This cleans out the ''

    # 3. Initialize search form data
    search_form_data = {
        'species': species_selected, # Now this will be a clean list (e.g., ['1', '2'] or [])
        'geneName': request.GET.get('geneName', ''),
        'pfamId': request.GET.get('pfamId', ''),
        'swissprot': request.GET.get('swissprot', ''),
        'go': request.GET.get('go', ''),
        'ec': request.GET.get('ec', ''),
        'kegg': request.GET.get('kegg', ''),
    }

    # CRITICAL SPEED FIX 1: Add select_related('species') to stop N+1 queries.
    # CRITICAL SPEED FIX 2: Order by 'gene_id' only (which is indexed) instead of across tables.
    gene_queryset = Gene.objects.select_related('species').filter(species__name_latin='Anethum graveolens').order_by('gene_id')
    
    # Check if ANY filter has data (including the species list)
    has_filters = any([
        search_form_data['species'], search_form_data['geneName'], 
        search_form_data['pfamId'], search_form_data['swissprot'], 
        search_form_data['go'], search_form_data['ec'], search_form_data['kegg']
    ])

    if request.method == 'GET' and has_filters:
        query = Q()
        
        # Multiple Species Filter
        if search_form_data['species']:
            # Use __in to search for any species matching the selected list
            query &= Q(species__taxonomy_id__in=search_form_data['species'])
            
        if search_form_data['geneName']:
            query &= Q(gene_id__icontains=search_form_data['geneName'])
        if search_form_data['pfamId']:
            query &= Q(pfam__icontains=search_form_data['pfamId'])
        if search_form_data['swissprot']:
            query &= Q(swissprot__icontains=search_form_data['swissprot'])
        if search_form_data['go']:
            query &= Q(go__icontains=search_form_data['go'])
        if search_form_data['ec']:
            query &= Q(ec__icontains=search_form_data['ec'])
        if search_form_data['kegg']:
            query &= Q(ko__icontains=search_form_data['kegg'])
        
        # Apply filters and maintain the fast select_related
        gene_queryset = Gene.objects.select_related('species').filter(query).order_by('gene_id')

    # 4. Pagination
    paginator = Paginator(gene_queryset, 20)
    page = request.GET.get('page')
    try:
        genes = paginator.page(page)
    except PageNotAnInteger:
        genes = paginator.page(1)
    except EmptyPage:
        genes = paginator.page(paginator.num_pages)

    # 5. Context
    context = {
        'species_choices': species_choices,
        'genes': genes,
        'search_form_data': search_form_data,
    }

    return render(request, 'home/gene_search.html', context=context)


def gene_detail(request, gene_id):
    gene = get_object_or_404(Gene, gene_id=gene_id)
    # 获取物种（关键修复）
    species = gene.species
    # Adjust window size
    start = max(gene.start - 1000, 1)
    end = gene.end + 1000
    # 开发环境使用 localhost
    static_server = "http://localhost:8001"
    jbrowse_url = (
        f"{static_server}/{species.browser_name}/"
        f"?assembly={species.browser_name}"
        f"&tracks={species.browser_name}_track"
        f"&loc={gene.chr}:{start}..{end}"
    )
    context = {
        "gene": gene,
        "go_terms": gene.go.split(";") if gene.go else [],
        "pfam_terms": gene.pfam.split(";") if gene.pfam else [],
        "ec_terms": gene.ec.split(";") if gene.ec else [],
        "ko_terms": gene.ko.split(";") if gene.ko else [],
        "jbrowse_url": jbrowse_url,
    }
    return render(request, "home/gene_detail.html", context)


# ========== 基因表达分析视图 ==========

def expression(request):
    form = ExpressionSearchForm(request.GET or None)
    table = None
    is_preview = False
    raw_data = []
    
    # We use a string for the massive DB count to avoid running a slow COUNT(*) query
    display_count = "18,362,633" 
    has_filters = False

    if request.GET and form.is_valid():
        cd = form.cleaned_data
        gene_ids = [g.strip() for g in cd.get('gene_id', '').split(',') if g.strip()]
        species_qs = cd.get('species')
        tissue_qs = cd.get('tissue')
        replicates = cd.get('replicate')
        min_exp = cd.get('min_expression')
        max_exp = cd.get('max_expression')

        if gene_ids or species_qs or tissue_qs or replicates or min_exp is not None or max_exp is not None:
            has_filters = True
            
            query = Q()
            if gene_ids:
                query &= Q(gene__gene_id__in=gene_ids)
            if species_qs:
                query &= Q(gene__species__in=species_qs)
            if tissue_qs:
                query &= Q(tissue__in=tissue_qs)
                
            if min_exp is not None:
                query &= Q(expression_value__gte=min_exp)
            if max_exp is not None:
                query &= Q(expression_value__lte=max_exp)

            queryset = GeneExpression.objects.filter(query)

            # ==========================================
            # 1. EXPORT LOGIC (Intercepted early!)
            # We handle the CSV before any capping occurs.
            # ==========================================
            if request.GET.get('export') == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="gene_expression_data.csv"'
                writer = csv.writer(response)
                writer.writerow(['Gene ID', 'Species', 'Tissue', 'Replicate', 'Expression (TPM)'])
                
                # If downloading selection, filter by IDs
                selected_ids = request.GET.get('ids')
                if selected_ids:
                    id_list = selected_ids.split(',')
                    queryset = queryset.filter(gene__gene_id__in=id_list)

                # Use .iterator() to stream the data efficiently without crashing RAM
                if replicates and "mean" in replicates:
                    export_qs = (
                        queryset.values('gene__gene_id', 'gene__species__name_latin', 'tissue__name')
                        .annotate(expression_value=Avg('expression_value'))
                        .order_by('gene__gene_id')
                        .iterator()
                    )
                    for row in export_qs:
                        val = round(float(row["expression_value"]), 2) if row["expression_value"] else 0.0
                        writer.writerow([row["gene__gene_id"], row["gene__species__name_latin"], row["tissue__name"], "Mean", val])
                else:
                    if replicates:
                        queryset = queryset.filter(replicate__in=[int(r) for r in replicates if r.isdigit()])
                    
                    export_qs = queryset.select_related('gene', 'tissue', 'gene__species').iterator()
                    for obj in export_qs:
                        val = round(float(obj.expression_value), 2) if obj.expression_value else 0.0
                        writer.writerow([obj.gene.gene_id, obj.gene.species.name_latin, obj.tissue.name, obj.replicate, val])
                
                # Return the file immediately, skipping table generation
                return response 

            # ==========================================
            # 2. WEBPAGE DISPLAY LOGIC
            # Cap at 2000 rows to keep the UI fast
            # ==========================================
            if replicates and "mean" in replicates:
                queryset = (
                    queryset.values('gene__gene_id', 'gene__species__name_latin', 'tissue__name')
                    .annotate(expression_value=Avg('expression_value'))
                    .order_by('gene__gene_id')
                )
                
                display_count = queryset.count()
                if display_count > 2000:
                    queryset = queryset[:2000]

                raw_data = [
                    {
                        "gene": row["gene__gene_id"],
                        "species": row["gene__species__name_latin"],
                        "tissue": row["tissue__name"],
                        "replicate": "Mean",
                        "value": round(float(row["expression_value"]), 2) if row["expression_value"] else 0.0
                    } for row in queryset
                ]
            else:
                queryset = queryset.select_related('gene', 'tissue', 'gene__species')
                if replicates: 
                    queryset = queryset.filter(replicate__in=[int(r) for r in replicates if r.isdigit()])
                
                display_count = queryset.count()
                if display_count > 2000:
                    queryset = queryset[:2000] 

                raw_data = [
                    {
                        "gene": obj.gene.gene_id,
                        "species": obj.gene.species.name_latin,
                        "tissue": obj.tissue.name,
                        "replicate": obj.replicate,
                        "value": round(float(obj.expression_value), 2) if obj.expression_value else 0.0
                    } for obj in queryset
                ]

    # --- PREVIEW LOGIC (If no filters are applied) ---
    if not has_filters:
        is_preview = True
        queryset = GeneExpression.objects.select_related('gene', 'tissue', 'gene__species')[:100]
        
        # Handle export if they click download on the preview page
        if request.GET.get('export') == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="gene_expression_preview.csv"'
            writer = csv.writer(response)
            writer.writerow(['Gene ID', 'Species', 'Tissue', 'Replicate', 'Expression (TPM)'])
            
            for obj in queryset:
                val = round(float(obj.expression_value), 2) if obj.expression_value else 0.0
                writer.writerow([obj.gene.gene_id, obj.gene.species.name_latin, obj.tissue.name, obj.replicate, val])
            return response
            
        # Normal preview HTML generation
        raw_data = [
            {
                "gene": obj.gene.gene_id,
                "species": obj.gene.species.name_latin,
                "tissue": obj.tissue.name,
                "replicate": obj.replicate,
                "value": round(float(obj.expression_value), 2) if obj.expression_value else 0.0
            } for obj in queryset
        ]
    # ==========================================
    # 3. CORRELATION HEATMAP VISUALIZATION
    # ==========================================
    heatmap_div = None
    can_generate_heatmap = False
    
    # Check if we have enough data to actually plot something
    if has_filters and raw_data and len(raw_data) > 1:
        can_generate_heatmap = True # Tell the template to show the button
        
        # Only run the heavy math if the user explicitly clicked the button
        if request.GET.get('show_correlation') == 'true':
            try:
                import pandas as pd
                import plotly.express as px

                df = pd.DataFrame(raw_data)
                
                pivot_df = df.pivot_table(
                    index='tissue', 
                    columns='gene', 
                    values='value', 
                    aggfunc='mean'
                )
                
                pivot_df = pivot_df.dropna(axis=1, how='all') 
                corr_matrix = pivot_df.corr()
                
                if not corr_matrix.empty and corr_matrix.shape[0] > 1 and corr_matrix.shape[1] > 1:
                    fig = px.imshow(
                        corr_matrix, 
                        text_auto=".2f",
                        aspect="auto",
                        color_continuous_scale='RdBu_r',
                        title="Gene Expression Correlation Heatmap (Pearson)",
                        labels=dict(color="Correlation")
                    )
                    fig.update_layout(margin=dict(t=50, l=20, r=20, b=20))
                    heatmap_div = fig.to_html(full_html=False, include_plotlyjs='cdn')
                else:
                    heatmap_div = "<div class='alert alert-info'>Not enough overlapping data points to calculate correlation. Try selecting more genes or tissues.</div>"
                    
            except Exception as e:
                heatmap_div = f"<div class='alert alert-warning'>Could not generate heatmap: {str(e)}</div>"

    # --- TABLE CREATION ---
    table = ExpressionTable(raw_data)
    RequestConfig(request, paginate={"per_page": 20}).configure(table)

    # Make sure to add `can_generate_heatmap` to your context dictionary!
    return render(request, "home/gene_express.html", {
        "form": form,
        "table": table,
        "display_count": display_count,
        "is_preview": is_preview,
        "heatmap_div": heatmap_div,
        "can_generate_heatmap": can_generate_heatmap, 
    })


def expression_samples(request):
    data = []
    
    # 1. Get all species
    species_list = Species.objects.all()
    
    for sp in species_list:
        # 2. Get the ID of just ONE gene for this species
        # Using values_list('id') makes this query take ~1 millisecond
        first_gene_id = Gene.objects.filter(species=sp).values_list('id', flat=True).first()
        
        if first_gene_id:
            # 3. Get the unique Tissues & Replicates for ONLY this one gene
            # Because it's a matrix, these are the samples for the whole species!
            samples = GeneExpression.objects.filter(gene_id=first_gene_id).values(
                'tissue__name', 
                'replicate'
            ).distinct().order_by('tissue__name', 'replicate')
            
            # 4. Format for the template
            for s in samples:
                data.append({
                    'species': sp.name_latin,
                    'tissue': s['tissue__name'],
                    'replicate': f"Rep {s['replicate']}"
                })

    return render(request, 'home/expression_samples.html', {'data': data})



# --- PAGE 1: PROFILE VIEW ---
class MetaboliteListView(FilterView):
    model = Metabolite
    filterset_class = MetaboliteFilter
    template_name = 'home/metabolite_profile.html' 
    paginate_by = 50
    ordering = ['compounds']

    def get(self, request, *args, **kwargs):
        # 1. Let the FilterView do its standard filtering setup first
        response = super().get(request, *args, **kwargs)
        
        # 2. Intercept the request if the user clicked an Export button
        if request.GET.get('export') == 'csv':
            # Get the fully filtered, unpaginated dataset
            queryset = self.filterset.qs 
            
            # If the user selected specific rows, filter down to just those IDs
            export_ids = request.GET.get('ids')
            if export_ids:
                queryset = queryset.filter(id__in=export_ids.split(','))
                
            # 3. Build the CSV file
            csv_response = HttpResponse(content_type='text/csv')
            csv_response['Content-Disposition'] = 'attachment; filename="metabolite_profile_dictionary.csv"'
            
            writer = csv.writer(csv_response)
            # Write the column headers
            writer.writerow(['ID', 'Compound Name', 'Chinese Name', 'Major Class', 'Sub Class', 'Formula', 'MW', 'RT', 'CAS', 'PubChem CID'])
            
            # Write the data rows
            for obj in queryset:
                writer.writerow([
                    obj.id, 
                    obj.compounds, 
                    obj.cn_name, 
                    obj.class_1, 
                    obj.class_2, 
                    obj.formula, 
                    obj.molecular_weight, 
                    obj.rt, 
                    obj.cas, 
                    obj.pubchem_cid,
                    obj.smile
                ])
            return csv_response
            
        # Return standard HTML page if not exporting
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table = MetaboliteTable(self.object_list)
        RequestConfig(self.request, paginate={'per_page': self.paginate_by}).configure(table)
        context['table'] = table
        context['total_count'] = self.object_list.count()
        return context


# --- PAGE 2: EXPRESSION VIEW ---
class MetaboliteExpressionListView(FilterView):
    model = MetaboliteExpression
    filterset_class = MetaboliteExpressionFilter
    template_name = 'home/metabolite_express.html'
    paginate_by = 50
    # FIX: We completely removed the cross-table ordering here to save 20 seconds!

    def get_queryset(self):
        # We only need select_related to grab the joined text. No order_by()!
        queryset = MetaboliteExpression.objects.all().select_related(
            'metabolite', 'species', 'tissue'
        )
        return queryset

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        # Intercept for CSV Export
        if request.GET.get('export') == 'csv':
            queryset = self.filterset.qs 
            
            export_ids = request.GET.get('ids')
            if export_ids:
                queryset = queryset.filter(id__in=export_ids.split(','))
                
            csv_response = HttpResponse(content_type='text/csv')
            csv_response['Content-Disposition'] = 'attachment; filename="metabolite_expression_data.csv"'
            
            import csv
            writer = csv.writer(csv_response)
            writer.writerow(['Expression ID', 'Compound', 'Species (Latin)', 'Tissue', 'Relative Amount Level'])
            
            # Using .iterator() prevents Django from loading all 1.2 million rows into your server's RAM at once during export!
            for obj in queryset.iterator():
                writer.writerow([
                    obj.id, 
                    obj.metabolite.compounds, 
                    obj.species.name_latin, 
                    obj.tissue.name, 
                    obj.relative_amount
                ])
            return csv_response
            
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table = MetaboliteExpressionTable(self.object_list)
        RequestConfig(self.request, paginate={'per_page': self.paginate_by}).configure(table)
        context['table'] = table
        context['total_count'] = f"{self.object_list.count():,}"
        return context



# ========== AMP search ==========
def antimicrobial_peptide(request):
    form = AmpSearchForm(request.GET or None)
    is_preview = False
    raw_data = []
    has_filters = False
    display_count = "1,065,649" # Smart Counting

    if request.GET and form.is_valid():
        cd = form.cleaned_data
        gene_ids = [g.strip() for g in cd.get('gene_id', '').split(',') if g.strip()]
        species_qs = cd.get('species')
        min_prob = cd.get('min_probability')
        max_prob = cd.get('max_probability')

        if gene_ids or species_qs or min_prob is not None or max_prob is not None:
            has_filters = True
            query = Q()
            
            if gene_ids:
                query &= Q(gene__gene_id__in=gene_ids)
            if species_qs:
                query &= Q(gene__species__in=species_qs)
            if min_prob is not None:
                query &= Q(amp_probability__gte=min_prob)
            if max_prob is not None:
                query &= Q(amp_probability__lte=max_prob)

            queryset = AntimicrobialPeptide.objects.filter(query).select_related('gene', 'gene__species')
            
            # Build data list
            raw_data = [{
                "smorf": obj.smorf_id,
                "gene": obj.gene.gene_id,
                "species": obj.gene.species.name_latin,
                "prob": round(obj.amp_probability, 4),
                "start": obj.start_pos,
                "end": obj.end_pos,
                "seq": obj.sequence
            } for obj in queryset]
            
            display_count = len(raw_data)

    if not has_filters:
        # CRITICAL: Lightning-Fast Preview Mode
        is_preview = True
        queryset = AntimicrobialPeptide.objects.select_related('gene', 'gene__species')[:100]
        raw_data = [{
            "smorf": obj.smorf_id,
            "gene": obj.gene.gene_id,
            "species": obj.gene.species.name_latin,
            "prob": round(obj.amp_probability, 4),
            "start": obj.start_pos,
            "end": obj.end_pos,
            "seq": obj.sequence
        } for obj in queryset]

    # --- DATA EXPORT ---
    if request.GET.get('export') == 'csv':
        from django_tables2.export.export import TableExport
        
        selected_ids = request.GET.get('ids')
        if selected_ids:
            id_list = selected_ids.split(',')
            raw_data = [row for row in raw_data if str(row['smorf']) in id_list]
            
        table_to_export = AmpTable(raw_data)
        exporter = TableExport("csv", table_to_export)
        return exporter.response("antimicrobial_peptides.csv")

    # --- TABLE CONFIG ---
    table = AmpTable(raw_data)
    RequestConfig(request, paginate={"per_page": 20}).configure(table)

    return render(request, "home/amp_search.html", {
        "form": form,
        "table": table,
        "is_preview": is_preview,
        "display_count": display_count,
        "has_filters": has_filters, # Passed to template for JS export warning
    })