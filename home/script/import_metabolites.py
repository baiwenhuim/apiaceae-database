import os, sys
import pandas as pd
from django.core.wsgi import get_wsgi_application
from django.db import transaction

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apiaceae.settings')
application = get_wsgi_application()

from home.models import Metabolite, MetaboliteExpression, Species, Tissue

BATCH_SIZE = 5000


def safe_float(value):
    try:
        return float(value)
    except:
        return None


def import_metabolite_info():
    df = pd.read_csv("metabolite_info.csv", encoding="utf-8-sig")

    metabolites = []

    for _, row in df.iterrows():
        metabolites.append(
            Metabolite(
                compounds=row["compounds"],
                cn_name=row.get("cn_name", ""),
                class_1=row.get("class_1", ""),
                class_2=row.get("class_2", ""),
                formula=row.get("formula", ""),
                molecular_weight=safe_float(row.get("molecular_weight")),
                rt=safe_float(row.get("rt")),
                score=safe_float(row.get("score")),
                cas=row.get("cas", ""),
                pubchem_cid=row.get("pubChem_cid", ""),
                smile=row.get("smile", ""),
            )
        )

    with transaction.atomic():
        Metabolite.objects.bulk_create(
            metabolites,
            batch_size=BATCH_SIZE,
            ignore_conflicts=True
        )

    print(f"✅ Imported {len(metabolites)} metabolites")


def import_metabolite_expression():
    df = pd.read_csv("metabolite_expression.csv", encoding="utf-8-sig")

    metabolite_map = {
        m.compounds.strip(): m for m in Metabolite.objects.all()
    }

    species_map = {
        s.taxonomy_id: s for s in Species.objects.all()
    }

    # preload tissue map
    tissue_map = {
        t.name.lower(): t for t in Tissue.objects.all()
    }

    expr_list = []
    new_tissue_count = 0
    missing_met = 0
    missing_species = 0

    for _, row in df.iterrows():

        compound_name = str(row["compounds"]).strip()

        met = metabolite_map.get(compound_name)
        if not met:
            missing_met += 1
            continue

        try:
            sp = species_map.get(int(row["species_code"]))
        except:
            missing_species += 1
            continue

        if not sp:
            missing_species += 1
            continue

        tissue_name = str(row["tissue_code"]).strip().lower()

        # 🔥 Auto-create tissue if not exist
        t = tissue_map.get(tissue_name)
        if not t:
            t = Tissue.objects.create(name=tissue_name)
            tissue_map[tissue_name] = t
            new_tissue_count += 1

        expr_list.append(
            MetaboliteExpression(
                metabolite=met,
                species=sp,
                tissue=t,
                relative_amount=safe_float(row["relative_amount"]),
            )
        )

        # optional: batch insert to reduce memory
        if len(expr_list) >= BATCH_SIZE:
            MetaboliteExpression.objects.bulk_create(
                expr_list,
                batch_size=BATCH_SIZE,
                ignore_conflicts=True
            )
            expr_list = []

    # final insert
    if expr_list:
        MetaboliteExpression.objects.bulk_create(
            expr_list,
            batch_size=BATCH_SIZE,
            ignore_conflicts=True
        )

    print(f"✅ Imported expression records")
    print(f"   Missing metabolite: {missing_met}")
    print(f"   Missing species: {missing_species}")
    print(f"   New tissues created: {new_tissue_count}")

if __name__ == "__main__":
    import_metabolite_info()
    import_metabolite_expression()
    print("🎉 All metabolite data imported successfully!")
