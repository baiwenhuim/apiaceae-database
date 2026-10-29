import os, sys
import pandas as pd
from django.core.wsgi import get_wsgi_application
from django.db import transaction
from django.db.models import Q
import re

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


def normalize_gene_id(gene_id: str) -> str:
    """
    尽可能把 gene_id 清理成最干净的基底形式（通常是 XXXGnnnn-RA 或 XXXGnnnn）
    处理以下几种常见脏后缀：
      1. .1.656edff2     → 去掉 .及后面全部
      2. -RA1656edffe    → 去掉 -RA 后面的连续数字/字母串（哈希或版本号）
      3. -RA.1.xxx       → 同 1
      4. 最后的 .数字    → 去掉
    """
    s = gene_id.strip()

    # 规则1：去掉 -RA 后面直接粘着的长数字/哈希串（至少5位，防止误伤正常短后缀）
    s = re.sub(r'(-RA)[0-9a-f]{5,}$', r'\1', s, flags=re.IGNORECASE)

    # 规则2：去掉 .数字.哈希 这种常见的可变剪接后缀
    s = re.sub(r'\.\d+\.[0-9a-f]+$', '', s)

    # 规则3：如果还有 .xxx 结尾，一并去掉（兜底）
    if '.' in s:
        s = s.split('.', 1)[0]

    # 规则4：极少数情况，最后还有 .数字
    s = re.sub(r'\.\d+$', '', s)

    return s.strip()


def import_amp():
    df = pd.read_csv(
        "amp_probability_ge_0.9.csv",
        encoding="utf-8-sig"
    )

    # 预加载 gene map（速度关键）
    gene_map = {
        g.gene_id: g
        for g in Gene.objects.select_related("species")
    }

    # 额外构建一个 “去掉后缀”的映射表，用于 fallback
    gene_map_no_suffix = {}
    for gene_id, gene_obj in gene_map.items():
        clean_id = normalize_gene_id(gene_id)
        if clean_id not in gene_map_no_suffix:
            gene_map_no_suffix[clean_id] = gene_obj
        # 如果有多个同前缀的，只保留第一个找到的（通常 pep 导入的是代表性本）

    amp_list = []
    missing_gene = 0
    missing_genes = set()
    fallback_count = 0

    for _, row in df.iterrows():
        original_gene_id = str(row["gene_id"]).strip()

        # 第一步：尝试完整匹配（最严格）
        gene = gene_map.get(original_gene_id)

        # 第二步：完整匹配失败 → 尝试去掉 . 后面的版本
        if not gene:
            clean_gene_id = normalize_gene_id(original_gene_id)
            gene = gene_map_no_suffix.get(clean_gene_id)
            if gene:
                fallback_count += 1

        if not gene:
            missing_gene += 1
            original = original_gene_id
            cleaned = normalize_gene_id(original_gene_id)
            missing_genes.add((original, cleaned))   # 同时存原始和清理版
            # 可选：打印出来方便排查
            # print(f"Missing gene: {original_gene_id}  (clean: {clean_gene_id})")
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
    print(f"Missing gene (完全匹配失败): {missing_gene}")
    print(f"使用去后缀 fallback 成功匹配: {fallback_count}")
    print(f"总处理行数: {len(df)}")
    print(f"\n缺失基因总数（去重后）: {len(missing_genes)}")
    print("前 30 个示例（原始 → 清理后）：")
    for i, (orig, clean) in enumerate(sorted(missing_genes)[:30], 1):
        print(f"{i:3d}. {orig:35} → {clean}")
    # 推荐：保存全部缺失列表，便于后续分析
    with open("missing_gene_ids.txt", "w", encoding="utf-8") as f:
        f.write("original_gene_id\tcleaned_gene_id\n")
        for orig, clean in sorted(missing_genes):
            f.write(f"{orig}\t{clean}\n")
    print("完整缺失列表已保存到：missing_gene_ids.txt")


if __name__ == "__main__":
    # ======================
    #   是否需要先清空旧数据？
    # ======================
    # 如果你希望本次导入完全覆盖旧数据（推荐大多数情况这样做）
    # 先把旧的全部删掉，避免出现重复或脏数据
    delete_before_import = True   # ← 根据需要改为 False

    if delete_before_import:
        print("正在清空旧的 AntimicrobialPeptide 数据...")
        AntimicrobialPeptide.objects.all().delete()
        print("旧数据已清空")

    import_amp()
