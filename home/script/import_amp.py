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

from home.models import AntimicrobialPeptide, Gene

BATCH_SIZE = 5000


def safe_float(v):
    try:
        return float(v)
    except:
        return None


def import_amp():

    df = pd.read_csv(
        "home/script/amp_probability_ge_0.9.csv",
        encoding="utf-8-sig"
    )

    # preload gene map (速度非常关键)
    gene_map = {
        g.gene_id: g
        for g in Gene.objects.select_related("species")
    }

    amp_list = []

    missing_gene = 0

    for _, row in df.iterrows():

        gene_id = str(row["gene_id"]).strip()

        gene = gene_map.get(gene_id)

        if not gene:
            missing_gene += 1
            continue

        amp_list.append(
            AntimicrobialPeptide(
                smorf_id=row["smorf"],
                gene=gene,
                sequence=row["sequence"],
                start_pos=int(row["start_pos"]),
                end_pos=int(row["end_pos"]),
                amp_probability=safe_float(row["amp_probability"]),
                prediction=row.get("prediction", "")
            )
        )

        if len(amp_list) >= BATCH_SIZE:

            AntimicrobialPeptide.objects.bulk_create(
                amp_list,
                batch_size=BATCH_SIZE,
                ignore_conflicts=True
            )

            amp_list = []

    if amp_list:
        AntimicrobialPeptide.objects.bulk_create(
            amp_list,
            batch_size=BATCH_SIZE,
            ignore_conflicts=True
        )

    print("✅ AMP import finished")
    print(f"Missing gene: {missing_gene}")


if __name__ == "__main__":
    import_amp()
