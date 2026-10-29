import os
import sys
import pandas as pd
from django.core.wsgi import get_wsgi_application
from django.db import transaction

# ======================
# 初始化 Django
# ======================
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../'))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apiaceae.settings')
application = get_wsgi_application()

from home.models import Species, Gene

# ======================
# 配置
# ======================
GENE_TSV = os.path.join(script_dir, "all_species_for_django.tsv")
CHUNK_SIZE = 50000

# ======================
# 简洁更新 + 新增
# ======================
def update_genes():
    print("\n🚀 开始更新 / 新增基因数据...")

    # 读取物种映射
    species_map = dict(Species.objects.values_list('taxonomy_id', 'id'))

    total_updated = 0
    total_created = 0
    chunk_num = 0

    for chunk in pd.read_csv(GENE_TSV, sep='\t', chunksize=CHUNK_SIZE, low_memory=False):
        chunk_num += 1
        print(f"\n→ 处理第 {chunk_num} 块...")

        with transaction.atomic():
            for _, row in chunk.iterrows():
                try:
                    # 读取关键字段
                    gene_id = str(row['gene_id']).strip()
                    sp_tax_id = int(row['species_id'])
                    sp_id = species_map[sp_tax_id]

                    # 准备要更新的所有字段
                    data = {
                        'chr': str(row['chr']).strip() if pd.notna(row['chr']) else "",
                        'start': int(row['start']) if pd.notna(row['start']) else 0,
                        'end': int(row['end']) if pd.notna(row['end']) else 0,
                        'strand': str(row['strand']).strip() if pd.notna(row['strand']) else "",
                        'pfam': str(row['pfam']).strip() if pd.notna(row['pfam']) else "",
                        'nr': str(row['nr']).strip() if pd.notna(row['nr']) else "",
                        'swissprot': str(row['swissprot']).strip() if pd.notna(row['swissprot']) else "",
                        'go': str(row['go']).strip() if pd.notna(row['go']) else "",
                        'ec': str(row['ec']).strip() if pd.notna(row['ec']) else "",
                        'ko': str(row['ko']).strip() if pd.notna(row['ko']) else "",
                        'clean_ec': str(row['clean_ec']).strip() if pd.notna(row['clean_ec']) else "",
                        'cds': str(row['cds']).strip() if pd.notna(row['cds']) else "",
                        'protein': str(row['protein']).strip() if pd.notna(row['protein']) else "",
                    }

                    # 查找并更新，不存在则创建
                    gene, created = Gene.objects.get_or_create(
                        gene_id=gene_id,
                        species_id=sp_id,
                        defaults=data
                    )

                    if created:
                        total_created += 1
                    else:
                        # 已存在 → 更新所有字段
                        for k, v in data.items():
                            setattr(gene, k, v)
                        gene.save()
                        total_updated += 1

                except Exception as e:
                    continue

        print(f"✅ 本块完成 → 已更新: {total_updated} | 已新增: {total_created}")

    print(f"\n🎉 全部完成！")
    print(f"✅ 已更新基因：{total_updated}")
    print(f"✅ 已新增基因：{total_created}")

if __name__ == "__main__":
    update_genes()