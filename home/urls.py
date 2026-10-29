from django.urls import path
from django.views.decorators.cache import cache_page
from home.views import general, search, tools
from home.views.search import MetaboliteExpressionListView, MetaboliteListView
from home.views.tools import PrimerDesignView, export_primers_excel

app_name = "home"
urlpatterns = [
    # ex: /home/
    path("", general.home_view, name="home"),  # landing page
    path("assembly/", general.assembly, name="assembly"),  # Assembly information
    path("jbrowse/", general.jbrowse, name="jbrowse"),  # Interactive genome browser
    path("blast/", tools.blast_tool, name="blast_tool"),
    path('enrichment/', tools.enrichment_tool, name='enrichment_tool'),
    path("userguide/", general.userguide, name="userguide"),
    path("contact_us/", general.contact_us, name="contact_us"),
    path('internal-review-portal/feedback/', general.feedback_list, name='feedback_list'), 
    path("download/", general.download_page, name="download"),
    # Custom route to securely serve files from the data/ folder
    path('download-file/<str:file_type>/<str:species_name>/', general.serve_data_file, name='download_file'),
    path('download-species-zip/<str:species_name>/', general.download_species_zip, name='download_species_zip'),
    path('download-all-zip/', general.download_all_zip, name='download_all_zip'),
    path("gene/", search.gene, name="gene"),  # Interface for gene search and download
    path("gene/<str:gene_id>/", search.gene_detail, name="gene_detail"),
    path("species/<str:normal_name>/", general.species, name="species"),  # Apiaceae species information
    path("metabolite/profile/", MetaboliteListView.as_view(), name='metabolite_profile'),
    path("metabolite/expression/", MetaboliteExpressionListView.as_view(), name='metabolite_expression'),
    path("amp/", search.antimicrobial_peptide, name="antimicrobial_peptide"),
    path("publications/", general.publications, name="publications"),  # Resources of publication
    path("wang_lab/", general.wang_lab, name="wang_lab"),  # The introduction of development lab
    path("expression/", search.expression, name="expression"),  # The expression of genes (TPM)
    path("expression_samples/", search.expression_samples, name="expression_samples"), # The samples of expression

    path('primer-design/', PrimerDesignView.as_view(), name='primer_design'),
    path('primer/export/', export_primers_excel, name='primer_export'),

    path("tools/hmmer/", tools.hmmer_tool_page, name="hmmer_input"),
    path("tools/hmmer/redirect/", tools.external_hmmer_redirect, name="hmmer_redirect"),

]
