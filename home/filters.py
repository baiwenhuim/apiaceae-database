from django import forms
import django_filters
from django_filters import FilterSet, ModelChoiceFilter, CharFilter, RangeFilter
from .models import Metabolite, MetaboliteExpression, Species, Tissue
from django_filters.widgets import RangeWidget


# 1. Profile Filter (For the general metabolite dictionary)
class MetaboliteFilter(FilterSet):
    compounds = CharFilter(
        lookup_expr='icontains', 
        label='Compound name',
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Pimpinellin', 'class': 'form-control'})
    )
    class_1 = CharFilter(
        lookup_expr='icontains',
        label='Major Class',
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Coumarins', 'class': 'form-control'})
    )
    class_2 = CharFilter(
        lookup_expr='icontains',
        label='Sub Class',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Metabolite
        fields = ['compounds', 'class_1', 'class_2']


class MetaboliteExpressionFilter(django_filters.FilterSet):
    # 1. Custom CharFilter for multiple comma-separated compounds
    metabolite__compounds = django_filters.CharFilter(
        method='filter_multiple_compounds',
        label='Compounds (comma-separated)',
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Vardenafil, Rutin'})
    )
    
    # 2. Multiple Choice Filter for Species
    species = django_filters.ModelMultipleChoiceFilter(
        queryset=Species.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '4'}),
        label='Species (hold Ctrl/Cmd to select multiple)'
    )
    
    # 3. Multiple Choice Filter for Tissues
    tissue = django_filters.ModelMultipleChoiceFilter(
        queryset=Tissue.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '4'}),
        label='Tissue (hold Ctrl/Cmd to select multiple)'
    )
    
    # 4. Standard Number range filters
    relative_amount_min = django_filters.NumberFilter(
        field_name='relative_amount', lookup_expr='gte', label='Min Abundance'
    )
    relative_amount_max = django_filters.NumberFilter(
        field_name='relative_amount', lookup_expr='lte', label='Max Abundance'
    )

    # Logic to split the comma-separated compounds and filter the database
    def filter_multiple_compounds(self, queryset, name, value):
        if not value:
            return queryset
        # Split string by comma and remove extra whitespace
        compounds = [c.strip() for c in value.split(',') if c.strip()]
        # Fetch records where the compound name matches ANY in the list
        return queryset.filter(metabolite__compounds__in=compounds)

    class Meta:
        model = MetaboliteExpression
        fields = ['metabolite__compounds', 'species', 'tissue', 'relative_amount_min', 'relative_amount_max']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # This forces the Species dropdown to use name_latin instead of the __str__ method!
        if 'species' in self.form.fields:
            self.form.fields['species'].label_from_instance = lambda obj: obj.name_latin