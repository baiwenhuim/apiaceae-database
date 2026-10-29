#!/usr/bin/env python3
"""
Export Gene Annotation Statistics per Species to CSV
Counts genes with non-empty annotations in: KO, EC, Pfam, NR, SwissProt, GO, Clean_EC
* Clean_EC: parse EC:xxx/SCORE → take MAX score per gene → test thresholds: ≥0.35 / ≥0.50 / ≥0.70
"""
import csv
import os
import re
from django.conf import settings

def extract_max_clean_ec(clean_ec_str):
    """
    Parse 'EC:3.1.4.53/0.0000,EC:3.4.11.9/0.9806' → return MAX score = 0.9806
    Returns None if no valid score found
    """
    if not clean_ec_str or not clean_ec_str.strip():
        return None
    scores = []
    # Match pattern: any digits.digits after /
    for part in clean_ec_str.split(','):
        part = part.strip()
        if '/' in part:
            try:
                score_str = part.rsplit('/', 1)[-1].strip()
                score = float(score_str)
                scores.append(score)
            except (ValueError, IndexError):
                continue
    return max(scores) if scores else None


def export_annotation_stats(output_path=None):
    from home.models import Gene

    if output_path is None:
        output_path = os.path.join(
            getattr(settings, 'BASE_DIR', '.'),
            "annotation_statistics.csv"
        )

    print("[INFO] Fetching gene data...")

    # Get all needed fields
    genes = Gene.objects.select_related('species').values(
        'species__taxonomy_id',
        'species__name_latin',
        'species__name_cn',
        'species__name_eng',
        'gene_id',
        'ko', 'ec', 'pfam', 'nr', 'swissprot', 'go', 'clean_ec'
    )

    from collections import defaultdict

    sp_data = defaultdict(lambda: {
        'total': set(),
        'ko': set(),
        'ec': set(),
        'pfam': set(),
        'nr': set(),
        'swissprot': set(),
        'go': set(),
        'clec_all': set(),
        'clec_035': set(),
        'clec_050': set(),
        'clec_070': set(),
    })

    species_info = {}  # cache species names

    for g in genes:
        tid = g['species__taxonomy_id']
        gid = g['gene_id']

        # Cache species info once
        if tid not in species_info:
            species_info[tid] = {
                'name_latin': g['species__name_latin'],
                'name_cn': g['species__name_cn'],
                'name_eng': g['species__name_eng'],
            }

        # Basic annotation counts (non-empty)
        sp_data[tid]['total'].add(gid)
        if g['ko'] and g['ko'].strip(): sp_data[tid]['ko'].add(gid)
        if g['ec'] and g['ec'].strip(): sp_data[tid]['ec'].add(gid)
        if g['pfam'] and g['pfam'].strip(): sp_data[tid]['pfam'].add(gid)
        if g['nr'] and g['nr'].strip(): sp_data[tid]['nr'].add(gid)
        if g['swissprot'] and g['swissprot'].strip(): sp_data[tid]['swissprot'].add(gid)
        if g['go'] and g['go'].strip(): sp_data[tid]['go'].add(gid)

        # Clean_EC parsing with thresholds
        max_score = extract_max_clean_ec(g['clean_ec'])
        if max_score is not None:
            sp_data[tid]['clec_all'].add(gid)
            if max_score >= 0.35:
                sp_data[tid]['clec_035'].add(gid)
            if max_score >= 0.50:
                sp_data[tid]['clec_050'].add(gid)
            if max_score >= 0.70:
                sp_data[tid]['clec_070'].add(gid)

    # Build sorted rows
    sorted_tids = sorted(
        sp_data.keys(),
        key=lambda x: (species_info[x]['name_latin'] or '').lower()
    )

    print(f"[INFO] Found {len(sorted_tids)} species. Writing CSV...")

    with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'Taxonomy ID',
            'Species Latin Name',
            'Species Name (CN)',
            'Species Name (EN)',
            'Total Genes',
            'KO Count',
            'EC Count',
            'Pfam Count',
            'NR Count',
            'SwissProt Count',
            'GO Count',
            'Clean EC (non-empty)',
            'Clean EC (≥0.35)',
            'Clean EC (≥0.50)',
            'Clean EC (≥0.70)',
        ])

        for tid in sorted_tids:
            d = sp_data[tid]
            info = species_info[tid]
            writer.writerow([
                tid,
                info['name_latin'] or '',
                info['name_cn'] or '',
                info['name_eng'] or '',
                len(d['total']),
                len(d['ko']),
                len(d['ec']),
                len(d['pfam']),
                len(d['nr']),
                len(d['swissprot']),
                len(d['go']),
                len(d['clec_all']),
                len(d['clec_035']),
                len(d['clec_050']),
                len(d['clec_070']),
            ])

    print(f"✅ Done! Saved to: {output_path}")
    return output_path


# Run directly
export_annotation_stats()
