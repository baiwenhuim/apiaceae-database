from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.views.decorators.http import require_http_methods
from django.core.files.temp import NamedTemporaryFile
from django.core.cache import cache
from django.conf import settings
from django.http import Http404, FileResponse
from django.contrib import messages

from home.forms import BlastForm, FeedbackForm
from home.models import Species, Gene, GeneExpression, AntimicrobialPeptide
from home.models import Feedback, Metabolite, MetaboliteExpression
from subprocess import run
import json
import os
import pandas as pd
import markdown


def home_view(request):
    
    # 1. Try to get the stats from the cache first
    stats_context = cache.get('homepage_db_stats')
    csv_path = os.path.join(settings.BASE_DIR, 'docs', 'stats.csv')
    df = pd.read_csv(csv_path)
    stats_context = {k: int(v) for k, v in zip(df['stat_name'], df['stat_value'])}
    stats_context['species_count'] = Species.objects.count()

    # 2. NEW: Read and render the Apiaceae introduction Markdown file
    filepath = os.path.join(settings.BASE_DIR, 'docs', 'apiaceae.md')
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            intro_text = f.read()
    except FileNotFoundError:
        intro_text = "Welcome to the Apiaceae Database."

    # Convert Markdown to HTML
    intro_html = markdown.markdown(intro_text)
    
    # 3. Add the HTML to the context dictionary
    stats_context['apiaceae_intro_html'] = intro_html
    
    return render(request, 'home/index.html', stats_context)


def species(request, normal_name):
    query_species = get_object_or_404(Species, name_latin=normal_name)
    
    # 构造上下文：直接传入模型对象（模板中可通过.访问字段）
    context = {'query_species': query_species}
    return render(request, 'home/species.html', context)

def assembly(request):
    species_list = Species.objects.all().order_by('name_latin')

    return render(request, 'home/assembly.html', {
        'species_list': species_list
    })



def jbrowse(request):
    species_list = Species.objects.all().order_by('name_latin')
    species_data = []
    
    # 开发环境使用 localhost
    static_server = "http://localhost:8001"
    
    for sp in species_list:
        jbrowse_url = (
            f"{static_server}/{sp.browser_name}/"
            f"?assembly={sp.browser_name}"
            f"&tracks={sp.browser_name}_track"
        )
        species_data.append({
            "latin": sp.name_latin,
            "chinese": sp.name_cn,
            "jbrowse_url": jbrowse_url,
        })
    
    return render(request, 'home/jbrowse.html', {'species_data': species_data})


def userguide(request):
    """Reads the Markdown user guide and renders it as HTML."""
    # Define the path to your markdown file
    filepath = os.path.join(settings.BASE_DIR, 'docs', 'userguide.md')
    
    # Read the markdown file
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        text = "# Error\nUser guide documentation file not found."

    # Convert Markdown to HTML (enabling tables and code blocks)
    html_content = markdown.markdown(text, extensions=['extra', 'tables', 'fenced_code', 'toc'])

    # Pass the converted HTML to the template
    return render(request, 'home/userguide.html', {'html_content': html_content})


def download_page(request):
    """Renders the download page with dynamic file paths for each species."""
    species_list = Species.objects.all().order_by('name_latin')
    download_data = []

    for sp in species_list:
        latin_name = sp.name_latin
        # Format: "Anethum_graveolens"
        name_under = latin_name.replace(' ', '_')

        download_data.append({
            'name_latin': latin_name,
            'name_under': name_under,
        })

    return render(request, 'home/download.html', {'download_data': download_data})


def serve_data_file(request, file_type, species_name):
    """Securely streams files from the data/ directory to the user."""
    base_dir = settings.BASE_DIR
    
    if file_type == 'cds':
        file_path = os.path.join(base_dir, 'data', 'apiaceae_cds', f"{species_name}.cds")
    elif file_type == 'pep':
        file_path = os.path.join(base_dir, 'data', 'apiaceae_pep', f"{species_name}.pep")
    elif file_type == 'assembly':
        file_path = os.path.join(base_dir, 'data', 'apiaceae_assembly', f"{species_name}.genome.fa.gz")
    elif file_type == 'gff':
        file_path = os.path.join(base_dir, 'data', 'apiaceae_gff', f"{species_name}.gff")
    elif file_type == 'gff_helixer':
        file_path = os.path.join(base_dir, 'data', 'apiaceae_helixer_gff', f"{species_name}_helixer.gff3")
    else:
        raise Http404("Invalid file type requested.")

    # Stream the file securely
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    else:
        raise Http404(f"File not found on server: {file_path}")


def download_species_zip(request, species_name):
    """Instantly serves the pre-zipped single species archive."""
    base_dir = settings.BASE_DIR
    zip_filename = f"{species_name}_complete_data.zip"
    zip_filepath = os.path.join(base_dir, 'data', 'archives', zip_filename)

    if os.path.exists(zip_filepath):
        return FileResponse(open(zip_filepath, 'rb'), as_attachment=True)
    else:
        raise Http404(f"Archive not found: {zip_filename}. Please contact the administrator.")


def download_all_zip(request):
    """Instantly serves the pre-zipped entire database archive."""
    base_dir = settings.BASE_DIR
    zip_filename = "Apiaceae_Database_COMPLETE.zip"
    zip_filepath = os.path.join(base_dir, 'data', 'archives', zip_filename)

    if os.path.exists(zip_filepath):
        return FileResponse(open(zip_filepath, 'rb'), as_attachment=True)
    else:
        raise Http404("Master database archive not found. Please contact the administrator.")

def publications(request):
    pass
    return render(request, "home/publications.html")


def wang_lab(request):
    pass
    return render(request, 'home/wang_lab.html')


def contact_us(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save() # Saves directly to the MySQL database
            # Send a success message to the template
            messages.success(request, 'Thank you! Your feedback has been submitted successfully.')
            return redirect('home:contact_us') # Refresh the page
    else:
        form = FeedbackForm()
    
    return render(request, 'home/contact.html', {'form': form})



def feedback_list(request):
    # Fetch all feedback from the database, ordered by newest first
    feedbacks = Feedback.objects.all().order_by('-created_at')
    
    return render(request, 'home/feedback_list.html', {'feedbacks': feedbacks})