import os
import sys
import pandas as pd
from django.core.wsgi import get_wsgi_application
from django.db import transaction

# --------------------------
# 初始化Django环境（必须放在最前面）
# --------------------------
# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
# 项目根目录（脚本目录向上两级）
project_root = os.path.abspath(os.path.join(script_dir, '../../'))
# 添加项目路径到Python环境
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# 设置Django配置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apiaceae.settings')
# 初始化Django
application = get_wsgi_application()

# 导入模型（必须在Django环境初始化后）
from home.models import Tissue, Gene, GeneExpression

# --------------------------
# 配置项（根据实际路径调整）
# --------------------------
# 文件路径
TISSUE_CSV_PATH = os.path.join(script_dir, "tissue.csv")
# EXPRESSION_TSV_PATH = os.path.join(script_dir, "gene_Agr10.tsv")
EXPRESSION_TSV_PATH = os.path.join(script_dir, "gene_expression.tsv")
# 批量大小（根据服务器内存调整，8G内存用10000，4G用5000）
BATCH_SIZE = 10000
# 分块大小（读取大文件时的分块，避免内存溢出）
CHUNK_SIZE = 50000

# --------------------------
# 工具函数：打印分隔线（美化日志）
# --------------------------
def print_separator(title):
    print(f"\n{'='*20} {title} {'='*20}")

# --------------------------
# 第一步：导入组织表数据
# --------------------------
def import_tissue_data():
    print_separator("开始导入组织表数据")
    
    # 1. 检查文件是否存在
    if not os.path.exists(TISSUE_CSV_PATH):
        print(f"❌ 错误：组织文件不存在 - {TISSUE_CSV_PATH}")
        return False
    
    # 2. 读取组织CSV文件
    try:
        # 处理UTF-8 BOM（避免表头乱码）
        df = pd.read_csv(
            TISSUE_CSV_PATH,
            encoding='utf-8-sig',
            skip_blank_lines=True,
            dtype=str  # 所有字段先按字符串读取，避免自动类型转换错误
        )
        print(f"✅ 成功读取组织文件，共 {len(df)} 行数据")
    except Exception as e:
        print(f"❌ 读取组织文件失败：{e}")
        return False
    
    # 3. 预查已存在的组织名（避免重复导入）
    existing_tissue_names = set(Tissue.objects.values_list("name", flat=True))
    print(f"ℹ️  数据库中已存在 {len(existing_tissue_names)} 个组织")
    
    # 4. 清洗并整理组织数据
    tissue_list = []
    skip_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        row_num = idx + 1  # 行号从1开始
        try:
            # 提取并清洗组织名（核心字段，必须唯一）
            tissue_name = str(row.get("name", "")).strip()
            if not tissue_name:
                skip_count += 1
                print(f"ℹ️  跳过第 {row_num} 行：组织名为空")
                continue
            # 转小写避免大小写重复（比如Root和root视为同一组织）
            tissue_name_lower = tissue_name.lower()
            if tissue_name_lower in existing_tissue_names:
                skip_count += 1
                print(f"ℹ️  跳过第 {row_num} 行：组织 {tissue_name} 已存在")
                continue
            
            # 提取描述（可选字段）
            tissue_desc = str(row.get("description", "")).strip() if pd.notna(row.get("description")) else ""
            
            # 添加到导入列表
            tissue_list.append(Tissue(
                name=tissue_name_lower,
                description=tissue_desc
            ))
            existing_tissue_names.add(tissue_name_lower)  # 避免同文件内重复
        
        except Exception as e:
            error_count += 1
            print(f"❌ 第 {row_num} 行数据错误：{e} | 原始数据：{row.to_dict()}")
            continue
    
    # 5. 批量插入组织数据
    if tissue_list:
        try:
            with transaction.atomic():  # 事务保证数据一致性
                Tissue.objects.bulk_create(tissue_list, batch_size=BATCH_SIZE)
            print(f"✅ 成功导入 {len(tissue_list)} 个新组织")
        except Exception as e:
            print(f"❌ 批量插入组织数据失败：{e}")
            return False
    else:
        print(f"ℹ️  无新组织数据可导入")
    
    # 6. 打印组织导入统计
    print_separator("组织表导入统计")
    print(f"📊 总数据行：{len(df)}")
    print(f"✅ 新增组织：{len(tissue_list)}")
    print(f"ℹ️  跳过数据：{skip_count}（已存在/为空）")
    print(f"❌ 错误数据：{error_count}")
    
    return True

# --------------------------
# 第二步：导入基因表达量表数据
# --------------------------
def import_expression_data():
    print_separator("开始导入基因表达量表数据")
    
    # 1. 检查文件是否存在
    if not os.path.exists(EXPRESSION_TSV_PATH):
        print(f"❌ 错误：表达量文件不存在 - {EXPRESSION_TSV_PATH}")
        return False
    
    # 2. 预加载基因/组织映射（内存查询，避免逐行查数据库）
    try:
        # 基因映射：{gene_id: 数据库主键ID}
        gene_map = dict(Gene.objects.values_list("gene_id", "id"))
        if not gene_map:
            print(f"❌ 错误：Gene表中无数据，请先导入基因数据")
            return False
        # 组织映射：{tissue_name: 数据库主键ID}
        tissue_map = dict(Tissue.objects.values_list("name", "id"))
        if not tissue_map:
            print(f"❌ 错误：Tissue表中无数据，请先导入组织数据")
            return False
        
        print(f"ℹ️  加载到 {len(gene_map)} 个基因ID映射")
        print(f"ℹ️  加载到 {len(tissue_map)} 个组织名映射")
    
    except Exception as e:
        print(f"❌ 加载基因/组织映射失败：{e}")
        return False
    
    # 3. 分块读取表达量TSV文件
    total_imported = 0
    total_skipped = 0
    total_error = 0
    chunk_num = 0
    
    try:
        # 逐块读取大文件，避免内存溢出
        for chunk in pd.read_csv(
            EXPRESSION_TSV_PATH,
            sep="\t",
            encoding='utf-8',
            skip_blank_lines=True,
            chunksize=CHUNK_SIZE,
            dtype=str  # 先按字符串读取，后续手动转换类型
        ):
            chunk_num += 1
            print(f"\nℹ️  处理第 {chunk_num} 块数据（共 {len(chunk)} 行）")
            
            # 清洗当前块数据
            expression_list = []
            chunk_skipped = 0
            chunk_error = 0
            
            for idx, row in chunk.iterrows():
                row_num_in_chunk = idx + 1
                global_row_num = (chunk_num - 1) * CHUNK_SIZE + row_num_in_chunk
                try:
                    # 提取核心字段并清洗
                    # a. 基因ID
                    gene_id = str(row.get("gene_id", "")).strip()
                    if not gene_id or gene_id not in gene_map:
                        chunk_skipped += 1
                        # 仅打印前10条跳过记录，避免日志过多
                        if chunk_skipped <= 10:
                            print(f"ℹ️  块{chunk_num}行{row_num_in_chunk}：基因 {gene_id} 不存在/为空，跳过")
                        continue
                    
                    # b. 组织名（转小写匹配tissue表）
                    tissue_name = str(row.get("tissue_name", "")).strip().lower()
                    if not tissue_name or tissue_name not in tissue_map:
                        chunk_skipped += 1
                        if chunk_skipped <= 10:
                            print(f"ℹ️  块{chunk_num}行{row_num_in_chunk}：组织 {tissue_name} 不存在/为空，跳过")
                        continue
                    
                    # c. 重复编号（转整数）
                    replicate_str = str(row.get("replicate", "1")).strip()
                    replicate = int(replicate_str) if replicate_str.isdigit() else 1
                    
                    # d. 表达量值（转浮点数，空值设为None）
                    expr_value_str = str(row.get("expression_value", "")).strip()
                    expression_value = float(expr_value_str) if expr_value_str and expr_value_str != "NA" else None
                    
                    # 组装表达量数据（移除unit字段）
                    expression_list.append(GeneExpression(
                        gene_id=gene_map[gene_id],          # 关联Gene表主键
                        tissue_id=tissue_map[tissue_name],  # 关联Tissue表主键
                        replicate=replicate,
                        expression_value=expression_value
                    ))
                
                except Exception as e:
                    chunk_error += 1
                    total_error += 1
                    # 仅打印前10条错误记录
                    if chunk_error <= 10:
                        print(f"❌ 块{chunk_num}行{row_num_in_chunk}：{e} | 原始数据：{row.to_dict()}")
                    continue
            
            # 批量插入当前块数据
            if expression_list:
                try:
                    with transaction.atomic():
                        # ignore_conflicts=True：忽略重复数据（避免unique_together约束报错）
                        GeneExpression.objects.bulk_create(
                            expression_list,
                            batch_size=BATCH_SIZE,
                            ignore_conflicts=True
                        )
                    imported_num = len(expression_list)
                    total_imported += imported_num
                    print(f"✅ 块{chunk_num}：成功导入 {imported_num} 条表达量数据")
                except Exception as e:
                    print(f"❌ 块{chunk_num}批量插入失败：{e} | 跳过该块 {len(expression_list)} 条数据")
                    total_skipped += len(expression_list)
            else:
                print(f"ℹ️  块{chunk_num}：无有效表达量数据")
            
            # 累计跳过数
            total_skipped += chunk_skipped
        
        # 打印总统计
        print_separator("表达量表导入统计")
        print(f"📊 处理块数：{chunk_num}")
        print(f"✅ 总计导入：{total_imported} 条")
        print(f"ℹ️  总计跳过：{total_skipped} 条（基因/组织不存在/重复）")
        print(f"❌ 总计错误：{total_error} 条")
        
        return True
    
    except Exception as e:
        print(f"❌ 读取表达量文件失败：{e}")
        return False

# --------------------------
# 主执行逻辑
# --------------------------
def main():
    print_separator("开始执行组织+表达量数据导入")
    
    # 第一步：导入组织数据
    tissue_import_success = import_tissue_data()
    if not tissue_import_success:
        print_separator("组织数据导入失败，终止流程")
        sys.exit(1)
    
    # 第二步：导入表达量数据
    expression_import_success = import_expression_data()
    if not expression_import_success:
        print_separator("表达量数据导入失败")
        sys.exit(1)
    
    # 导入完成
    print_separator("所有数据导入完成！")
    print("✅ 组织表和表达量表数据导入成功")
    print("ℹ️  可通过以下命令验证数据：")
    print("   python manage.py shell")
    print("   from home.models import Tissue, GeneExpression")
    print("   print('组织数：', Tissue.objects.count())")
    print("   print('表达量数据数：', GeneExpression.objects.count())")

if __name__ == "__main__":
    main()
