import os
import sys
import pandas as pd
from django.core.wsgi import get_wsgi_application

# --------------------------
# 关键新增：添加项目根目录到Python路径，解决ModuleNotFoundError
# --------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --------------------------
# 初始化Django环境（必须）
# --------------------------
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apiaceae.settings')
application = get_wsgi_application()

# 仅导入需要的模型，彻底移除所有无用模型（避免Tissue表依赖）
from home.models import Species, Gene

# --------------------------
# 配置文件路径
# --------------------------
SPECIES_CSV_PATH = os.path.join(script_dir, "species.csv")
GENE_TSV_PATH = os.path.join(script_dir, "gene.tsv")

# --------------------------
# 导入物种数据（核心修复：优先处理所有带格式的字段，避免提前转int报错）
# --------------------------
def import_species():
    """导入物种数据（修复gene_count逗号处理，避免int转换报错）"""
    if not os.path.exists(SPECIES_CSV_PATH):
        print(f"错误：物种CSV文件不存在，请检查路径：{SPECIES_CSV_PATH}")
        return

    try:
        # 处理BOM头，读取CSV
        df = pd.read_csv(
            SPECIES_CSV_PATH,
            encoding='utf-8-sig',
            skip_blank_lines=True
        )
    except Exception as e:
        print(f"错误：读取物种CSV文件失败，原因：{e}")
        return

    # 检查必要字段
    required_fields = ["taxonomy_id"]
    for field in required_fields:
        if field not in df.columns:
            print(f"错误：物种CSV缺少必要字段：{field}")
            return

    success_count = 0
    fail_count = 0

    for _, row in df.iterrows():
        try:
            # 步骤1：先提取所有字段为字符串，避免提前触发类型转换
            taxonomy_id_str = str(row["taxonomy_id"]).strip() if pd.notna(row["taxonomy_id"]) else ""
            name_cn = str(row["name_cn"]).strip() if "name_cn" in df.columns and pd.notna(row["name_cn"]) else ""
            name_latin = str(row["name_latin"]).strip() if "name_latin" in df.columns and pd.notna(row["name_latin"]) else ""
            genus = str(row["genus"]).strip() if "genus" in df.columns and pd.notna(row["genus"]) else ""
            genome_size_str = str(row["genome_size"]).strip() if "genome_size" in df.columns and pd.notna(row["genome_size"]) else ""
            gene_count_str = str(row["gene_count"]).strip() if "gene_count" in df.columns and pd.notna(row["gene_count"]) else ""
            chromosome_number = str(row["chromosome_number"]).strip() if "chromosome_number" in df.columns and pd.notna(row["chromosome_number"]) else ""
            geographical_distribution = str(row["geographical_distribution"]).strip() if "geographical_distribution" in df.columns and pd.notna(row["geographical_distribution"]) else ""
            description = str(row["description"]).strip() if "description" in df.columns and pd.notna(row["description"]) else ""
            species_pic_path = str(row["species_pic_path"]).strip() if "species_pic_path" in df.columns and pd.notna(row["species_pic_path"]) else ""

            # 步骤2：单独处理数字类型字段，清洗格式后再转换
            # 处理taxonomy_id（转int）
            if not taxonomy_id_str.isdigit():
                print(f"跳过：无效的taxonomy_id - {taxonomy_id_str}（非纯数字）")
                fail_count += 1
                continue
            taxonomy_id = int(taxonomy_id_str)

            # 处理genome_size（转float，空值/无效值设为None）
            genome_size = None
            if genome_size_str and genome_size_str.replace(".", "", 1).isdigit():
                genome_size = float(genome_size_str)

            # 处理gene_count（先去逗号，再转int，空值/无效值设为None）
            gene_count = None
            if gene_count_str:
                gene_count_clean = gene_count_str.replace(",", "").strip()  # 核心修复：移除逗号
                if gene_count_clean.isdigit():
                    gene_count = int(gene_count_clean)

            # 步骤3：创建或获取物种（此时所有字段格式已清洗，无转换报错）
            Species.objects.get_or_create(
                taxonomy_id=taxonomy_id,
                defaults={
                    "name_cn": name_cn,
                    "name_latin": name_latin,
                    "genus": genus,
                    "genome_size": genome_size,
                    "gene_count": gene_count,
                    "chromosome_number": chromosome_number,
                    "geographical_distribution": geographical_distribution,
                    "description": description,
                    "species_pic_path": species_pic_path
                }
            )

            success_count += 1
        except Exception as e:
            print(f"跳过：物种导入失败 - Taxonomy ID: {row.get('taxonomy_id', 'Unknown')}，原因：{str(e)}")
            fail_count += 1

    print(f"物种数据导入完成！成功：{success_count}条，失败：{fail_count}条")

# --------------------------
# 导入基因数据（保持不变，确保依赖物种导入成功）
# --------------------------
def import_genes():
    """导入基因数据（适配TSV格式，字段映射：species_id → taxonomy_id）"""
    if not os.path.exists(GENE_TSV_PATH):
        print(f"错误：基因TSV文件不存在，请检查路径：{GENE_TSV_PATH}")
        return

    try:
        df = pd.read_csv(
            GENE_TSV_PATH,
            sep="\t",
            encoding="utf-8",
            skip_blank_lines=True
        )
    except Exception as e:
        print(f"错误：读取基因TSV文件失败，原因：{e}")
        return

    required_fields = ["gene_id", "species_id", "chr", "start", "end", "strand"]
    for field in required_fields:
        if field not in df.columns:
            print(f"错误：基因TSV缺少必要字段：{field}")
            return

    success_count = 0
    fail_count = 0

    for _, row in df.iterrows():
        try:
            gene_id = str(row["gene_id"]).strip() if pd.notna(row["gene_id"]) else ""
            species_id_str = str(row["species_id"]).strip() if pd.notna(row["species_id"]) else ""

            # 验证species_id是否为纯数字
            if not gene_id or not species_id_str.isdigit():
                fail_count += 1
                continue
            species_id = int(species_id_str)

            chr_num = str(row["chr"]).strip() if pd.notna(row["chr"]) else ""
            start = int(row["start"]) if pd.notna(row["start"]) else 0
            end = int(row["end"]) if pd.notna(row["end"]) else 0
            strand = str(row["strand"]).strip() if pd.notna(row["strand"]) else ""
            pfam = str(row["pfam"]).strip() if "pfam" in df.columns and pd.notna(row["pfam"]) else ""
            nr = str(row["nr"]).strip() if "nr" in df.columns and pd.notna(row["nr"]) else ""
            swissprot = str(row["swissprot"]).strip() if "swissprot" in df.columns and pd.notna(row["swissprot"]) else ""
            go = str(row["go"]).strip() if "go" in df.columns and pd.notna(row["go"]) else ""
            ec = str(row["ec"]).strip() if "ec" in df.columns and pd.notna(row["ec"]) else ""
            ko = str(row["ko"]).strip() if "ko" in df.columns and pd.notna(row["ko"]) else ""
            clean_ec = str(row["clean_ec"]).strip() if "clean_ec" in df.columns and pd.notna(row["clean_ec"]) else ""

            # 获取物种（仅当物种导入成功后才会存在）
            species = Species.objects.get(taxonomy_id=species_id)

            Gene.objects.get_or_create(
                gene_id=gene_id,
                species=species,
                defaults={
                    "chr": chr_num,
                    "start": start,
                    "end": end,
                    "strand": strand,
                    "pfam": pfam,
                    "nr": nr,
                    "swissprot": swissprot,
                    "go": go,
                    "ec": ec,
                    "ko": ko,
                    "clean_ec": clean_ec
                }
            )

            success_count += 1
        except Species.DoesNotExist:
            print(f"跳过：物种不存在 - Species ID: {row.get('species_id', 'Unknown')}，基因ID：{row.get('gene_id', 'Unknown')}")
            fail_count += 1
        except Exception as e:
            print(f"跳过：基因导入失败 - {row.get('gene_id', 'Unknown')}，原因：{str(e)}")
            fail_count += 1

    print(f"基因数据导入完成！成功：{success_count}条，失败：{fail_count}条")

# --------------------------
# 执行导入（仅物种+基因，彻底避免Tissue表依赖）
# --------------------------
if __name__ == "__main__":
    try:
        print("开始导入数据...")
        import_species()
        # 仅当物种导入成功后，再执行基因导入（可选，按需开启）
        import_genes()
        print("\n所有指定数据导入流程执行完毕！")
    except Exception as e:
        print(f"\n数据导入流程异常终止，原因：{str(e)}")
