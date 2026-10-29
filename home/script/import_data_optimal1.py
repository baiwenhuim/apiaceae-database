import os
import sys
import pandas as pd
from django.core.wsgi import get_wsgi_application
from django.db import transaction

# --------------------------
# 初始化Django环境 + 添加项目路径
# --------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apiaceae.settings')
application = get_wsgi_application()

from home.models import Species, Gene

# --------------------------
# 配置（可根据服务器性能调整批次大小）
# --------------------------
SPECIES_CSV_PATH = os.path.join(script_dir, "species.csv")
GENE_TSV_PATH = os.path.join(script_dir, "gene.tsv")
BATCH_SIZE = 10000  # 每批次导入1万条（服务器内存小可改5000，大则改20000）
CHUNK_SIZE = 50000  # 读取TSV时的分块大小（避免一次性加载160万条占满内存）

# --------------------------
# 优化1：批量导入物种（增强异常处理+打印错误数据详情）
# --------------------------
def import_species_batch():
    if not os.path.exists(SPECIES_CSV_PATH):
        print(f"错误：物种CSV文件不存在 - {SPECIES_CSV_PATH}")
        return

    try:
        # 一次性读取所有物种数据（物种数据量少，无需分块）
        df = pd.read_csv(
            SPECIES_CSV_PATH,
            encoding='utf-8-sig',
            skip_blank_lines=True
        )
    except Exception as e:
        print(f"读取物种CSV失败：{e}")
        return

    # 步骤1：清洗物种数据，生成待导入的字典列表
    species_list = []
    valid_taxonomy_ids = []
    error_species_count = 0  # 统计错误物种数

    for idx, row in df.iterrows():
        try:
            # 提取原始行数据（用于错误打印）
            raw_row = row.to_dict()
            taxonomy_id_str = str(row.get("taxonomy_id", "")).strip()
            
            # 校验taxonomy_id格式
            if not taxonomy_id_str or not taxonomy_id_str.isdigit():
                error_species_count += 1
                print(f"\n【物种数据无效】行号：{idx+1} | 错误原因：taxonomy_id非数字或为空")
                print(f"原始数据：{raw_row}")
                continue
            
            taxonomy_id = int(taxonomy_id_str)

            # 清洗字段（逐个字段校验，避免类型转换报错）
            species_data = {}
            try:
                species_data["taxonomy_id"] = taxonomy_id
                species_data["name_cn"] = str(row["name_cn"]).strip() if pd.notna(row["name_cn"]) else ""
                species_data["name_latin"] = str(row["name_latin"]).strip() if pd.notna(row["name_latin"]) else ""
                species_data["genus"] = str(row["genus"]).strip() if pd.notna(row["genus"]) else ""
                
                # genome_size 类型转换容错
                genome_size_val = row["genome_size"] if "genome_size" in df.columns else None
                species_data["genome_size"] = float(genome_size_val) if pd.notna(genome_size_val) else None
                
                # gene_count 去逗号+类型转换容错
                gene_count_val = str(row["gene_count"]).replace(",", "").strip() if "gene_count" in df.columns and pd.notna(row["gene_count"]) else ""
                species_data["gene_count"] = int(gene_count_val) if gene_count_val.isdigit() else None
                
                species_data["chromosome_number"] = str(row["chromosome_number"]).strip() if pd.notna(row["chromosome_number"]) else ""
                species_data["geographical_distribution"] = str(row["geographical_distribution"]).strip() if pd.notna(row["geographical_distribution"]) else ""
                species_data["description"] = str(row["description"]).strip() if pd.notna(row["description"]) else ""
                species_data["species_pic_path"] = str(row["species_pic_path"]).strip() if pd.notna(row["species_pic_path"]) else ""
                
            except Exception as field_e:
                error_species_count += 1
                print(f"\n【物种字段解析失败】行号：{idx+1} | taxonomy_id：{taxonomy_id_str} | 错误原因：{field_e}")
                print(f"原始数据：{raw_row}")
                continue

            species_list.append(species_data)
            valid_taxonomy_ids.append(taxonomy_id)
            
        except Exception as row_e:
            error_species_count += 1
            print(f"\n【物种行处理失败】行号：{idx+1} | 错误原因：{row_e}")
            print(f"原始数据：{row.to_dict()}")
            continue

    # 步骤2：批量查询已存在的物种ID（仅1次数据库查询，替代逐行查询）
    try:
        existing_taxonomy_ids = set(Species.objects.filter(taxonomy_id__in=valid_taxonomy_ids).values_list("taxonomy_id", flat=True))
    except Exception as e:
        print(f"\n【查询已存在物种失败】错误原因：{e} | 跳过物种批量创建")
        return

    # 步骤3：批量创建新物种（事务包裹+异常捕获，失败不终止）
    new_species = []
    for species_data in species_list:
        if species_data["taxonomy_id"] not in existing_taxonomy_ids:
            new_species.append(Species(**species_data))

    if new_species:
        try:
            with transaction.atomic():  # 事务保证要么全成功，要么全失败
                Species.objects.bulk_create(new_species, batch_size=BATCH_SIZE)
            print(f"\n批量导入物种完成：新增 {len(new_species)} 条，跳过已存在 {len(existing_taxonomy_ids)} 条，无效数据 {error_species_count} 条")
        except Exception as bulk_e:
            # 批量插入失败时，拆分批次重试+打印错误批次数据
            print(f"\n【物种批量插入失败】错误原因：{bulk_e} | 尝试拆分批次重试...")
            # 拆分小批次重试，定位具体错误数据
            failed_batch = []
            for i in range(0, len(new_species), 1000):
                batch = new_species[i:i+1000]
                try:
                    with transaction.atomic():
                        Species.objects.bulk_create(batch, batch_size=1000)
                    print(f"小批次 {i//1000 + 1} 插入成功（{len(batch)} 条）")
                except Exception as small_batch_e:
                    failed_batch.extend(batch)
                    print(f"【小批次插入失败】批次 {i//1000 + 1} | 错误原因：{small_batch_e}")
                    print(f"失败批次数据示例：{batch[0].__dict__ if batch else '无'}")
            print(f"物种导入最终结果：成功 {len(new_species)-len(failed_batch)} 条，失败 {len(failed_batch)} 条，无效数据 {error_species_count} 条")
    else:
        print(f"\n所有物种已存在，无需导入 | 无效数据 {error_species_count} 条")

# --------------------------
# 优化2：分块读取+批量导入基因（增强异常处理+打印错误数据详情）
# --------------------------
def import_genes_batch():
    if not os.path.exists(GENE_TSV_PATH):
        print(f"错误：基因TSV文件不存在 - {GENE_TSV_PATH}")
        return

    # 步骤1：先加载所有物种ID到内存（仅1次查询，避免逐行查物种）
    try:
        species_map = dict(Species.objects.values_list("taxonomy_id", "id"))  # {taxonomy_id: 物种主键ID}
        if not species_map:
            print("错误：无物种数据，请先导入物种")
            return
    except Exception as e:
        print(f"\n【查询物种映射失败】错误原因：{e} | 跳过基因导入")
        return

    # 步骤2：分块读取TSV（避免一次性加载160万条占满内存）
    chunk_num = 0
    total_imported = 0
    total_skipped = 0
    total_error = 0

    # 逐块读取TSV文件（外层try-except避免分块读取终止）
    try:
        for chunk in pd.read_csv(
            GENE_TSV_PATH,
            sep="\t",
            encoding="utf-8",
            skip_blank_lines=True,
            chunksize=CHUNK_SIZE  # 每次读取5万条，分块处理
        ):
            chunk_num += 1
            print(f"\n========== 开始处理第 {chunk_num} 块数据（每块 {CHUNK_SIZE} 条）==========")
            
            # 步骤3：清洗当前块的基因数据
            gene_list = []
            valid_gene_ids = []
            valid_species_ids = []
            chunk_error = 0

            for idx, row in chunk.iterrows():
                try:
                    # 提取原始行数据+行号（用于错误打印）
                    raw_row = row.to_dict()
                    row_num = idx + 1  # 显示实际行号（含之前块的累计）
                    
                    # 基础字段清洗+校验
                    gene_id = str(row.get("gene_id", "")).strip()
                    species_id_str = str(row.get("species_id", "")).strip()

                    # 校验gene_id和species_id
                    if not gene_id:
                        total_skipped += 1
                        chunk_error += 1
                        print(f"\n【基因数据无效】块{chunk_num}行{row_num} | 错误原因：gene_id为空")
                        print(f"原始数据：{raw_row}")
                        continue
                    
                    if not species_id_str.isdigit():
                        total_skipped += 1
                        chunk_error += 1
                        print(f"\n【基因数据无效】块{chunk_num}行{row_num} | gene_id：{gene_id} | 错误原因：species_id非数字")
                        print(f"原始数据：{raw_row}")
                        continue

                    species_id = int(species_id_str)
                    # 检查物种是否存在（内存中查询，无数据库IO）
                    if species_id not in species_map:
                        total_skipped += 1
                        chunk_error += 1
                        print(f"\n【基因数据无效】块{chunk_num}行{row_num} | gene_id：{gene_id} | 错误原因：species_id {species_id} 不存在")
                        print(f"原始数据：{raw_row}")
                        continue

                    # 组装基因数据（逐个字段容错）
                    gene_data = {}
                    try:
                        gene_data["gene_id"] = gene_id
                        gene_data["species_id"] = species_map[species_id]
                        gene_data["chr"] = str(row["chr"]).strip() if pd.notna(row["chr"]) else ""
                        gene_data["start"] = int(row["start"]) if pd.notna(row["start"]) else 0
                        gene_data["end"] = int(row["end"]) if pd.notna(row["end"]) else 0
                        gene_data["strand"] = str(row["strand"]).strip() if pd.notna(row["strand"]) else ""
                        gene_data["pfam"] = str(row["pfam"]).strip() if "pfam" in chunk.columns and pd.notna(row["pfam"]) else ""
                        gene_data["nr"] = str(row["nr"]).strip() if "nr" in chunk.columns and pd.notna(row["nr"]) else ""
                        gene_data["swissprot"] = str(row["swissprot"]).strip() if "swissprot" in chunk.columns and pd.notna(row["swissprot"]) else ""
                        gene_data["go"] = str(row["go"]).strip() if "go" in chunk.columns and pd.notna(row["go"]) else ""
                        gene_data["ec"] = str(row["ec"]).strip() if "ec" in chunk.columns and pd.notna(row["ec"]) else ""
                        gene_data["ko"] = str(row["ko"]).strip() if "ko" in chunk.columns and pd.notna(row["ko"]) else ""
                        gene_data["clean_ec"] = str(row["clean_ec"]).strip() if "clean_ec" in chunk.columns and pd.notna(row["clean_ec"]) else ""
                    except Exception as field_e:
                        total_skipped += 1
                        chunk_error += 1
                        print(f"\n【基因字段解析失败】块{chunk_num}行{row_num} | gene_id：{gene_id} | 错误原因：{field_e}")
                        print(f"原始数据：{raw_row}")
                        continue

                    gene_list.append(gene_data)
                    valid_gene_ids.append(gene_id)
                    valid_species_ids.append(species_map[species_id])
                    
                except Exception as row_e:
                    total_skipped += 1
                    chunk_error += 1
                    total_error += 1
                    print(f"\n【基因行处理失败】块{chunk_num}行{idx+1} | 错误原因：{row_e}")
                    print(f"原始数据：{row.to_dict()}")
                    continue

            # 步骤4：批量查询当前块已存在的基因（仅1次数据库查询/块）
            try:
                existing_genes = set(
                    Gene.objects.filter(
                        gene_id__in=valid_gene_ids,
                        species_id__in=valid_species_ids
                    ).values_list("gene_id", "species_id")  # 组合主键：gene_id + species_id
                )
            except Exception as e:
                print(f"\n【查询已存在基因失败】块{chunk_num} | 错误原因：{e} | 跳过该块基因导入")
                total_skipped += len(gene_list)
                continue

            # 步骤5：筛选出需要新增的基因
            new_genes = []
            for gene_data in gene_list:
                gene_key = (gene_data["gene_id"], gene_data["species_id"])
                if gene_key not in existing_genes:
                    new_genes.append(Gene(**gene_data))

            # 步骤6：批量插入当前块的新基因（事务包裹+异常捕获，失败不终止）
            if new_genes:
                try:
                    with transaction.atomic():
                        Gene.objects.bulk_create(new_genes, batch_size=BATCH_SIZE)  # 批量插入
                    imported = len(new_genes)
                    total_imported += imported
                    print(f"\n第 {chunk_num} 块处理完成：新增 {imported} 条，跳过已存在 {len(gene_list)-imported} 条，无效数据 {chunk_error} 条")
                except Exception as bulk_e:
                    print(f"\n【基因批量插入失败】块{chunk_num} | 错误原因：{bulk_e} | 跳过该块 {len(new_genes)} 条基因")
                    print(f"失败批次数据示例：{new_genes[0].__dict__ if new_genes else '无'}")
                    total_skipped += len(new_genes)
            else:
                print(f"\n第 {chunk_num} 块无新基因，全部跳过 | 无效数据 {chunk_error} 条")

            total_skipped += len(gene_list) - len(new_genes)
    
    except Exception as chunk_e:
        print(f"\n【基因分块读取失败】错误原因：{chunk_e} | 终止分块处理，但已处理的块不受影响")

    # 最终统计
    print(f"\n==================== 基因导入统计 ====================")
    print(f"总计新增：{total_imported} 条")
    print(f"总计跳过：{total_skipped} 条（已存在/无效数据/插入失败）")
    print(f"总计处理错误：{total_error} 条")

# --------------------------
# 主执行逻辑（顶级异常捕获，确保任何错误不终止流程）
# --------------------------
if __name__ == "__main__":
    print("========== 开始批量导入数据（增强容错版）==========")
    # 先导入物种（批量）
    try:
        import_species_batch()
    except Exception as species_e:
        print(f"\n【物种导入流程异常】错误原因：{species_e} | 继续执行基因导入...")
    
    # 再分块导入基因（核心优化）
    try:
        import_genes_batch()
    except Exception as gene_e:
        print(f"\n【基因导入流程异常】错误原因：{gene_e}")
    
    print("\n========== 所有数据导入流程执行完毕（部分数据可能失败，详见日志）==========")
