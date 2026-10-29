import os
import sys
import pandas as pd
from django.core.wsgi import get_wsgi_application
from django.db import transaction

# --------------------------
# 初始化 Django 环境
# --------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apiaceae.settings')
application = get_wsgi_application()

from home.models import Species

# --------------------------
# 配置
# --------------------------
SPECIES_CSV_PATH = os.path.join(script_dir, "species.csv")

def update_all_species():
    print("\n🚀 开始全量更新物种信息...")
    df = pd.read_csv(SPECIES_CSV_PATH, encoding='utf-8-sig')
    
    # 统计信息
    updated_count = 0
    created_count = 0
    error_count = 0
    skipped_count = 0
    
    for _, row in df.iterrows():
        try:
            tax_id = int(row['taxonomy_id'])
            
            # 辅助函数：安全获取字符串值
            def get_str_value(col_name):
                if col_name in df.columns and pd.notna(row[col_name]):
                    value = str(row[col_name]).strip()
                    return value if value and value != 'nan' else ''
                return ''
            
            # 辅助函数：安全获取整数值
            def get_int_value(col_name):
                if col_name in df.columns and pd.notna(row[col_name]):
                    try:
                        # 处理带逗号的数字，如 "1,269,927,931"
                        value_str = str(row[col_name]).strip().replace(',', '')
                        if value_str and value_str != 'nan':
                            return int(float(value_str))
                    except (ValueError, TypeError):
                        pass
                return None
            
            # 辅助函数：安全获取浮点数值
            def get_float_value(col_name):
                if col_name in df.columns and pd.notna(row[col_name]):
                    try:
                        value_str = str(row[col_name]).strip().replace(',', '')
                        if value_str and value_str != 'nan':
                            return float(value_str)
                    except (ValueError, TypeError):
                        pass
                return None
            
            # 辅助函数：安全获取Decimal值（用于BUSCO）
            def get_decimal_value(col_name):
                value = get_float_value(col_name)
                if value is not None:
                    from decimal import Decimal
                    return Decimal(str(round(value, 2)))
                return None
            
            # 准备所有字段的默认值
            defaults = {
                'name_cn': get_str_value('name_cn'),
                'name_latin': get_str_value('name_latin'),
                'name_eng': get_str_value('name_eng'),
                'genus': get_str_value('genus'),
                'description': get_str_value('description'),
                'geographical_distribution': get_str_value('geographical_distribution'),
                'species_pic_path': get_str_value('species_pic_path'),
                'image_copyright': get_str_value('image_copyright'),
                'chromosome_number': get_str_value('chromosome_number'),
            }
            
            # 数字类型字段（允许NULL）
            genome_size_bp = get_int_value('genome_size_bp')
            if genome_size_bp is not None:
                defaults['genome_size_bp'] = genome_size_bp
            
            n50 = get_int_value('n50')
            if n50 is not None:
                defaults['n50'] = n50
            
            gene_count = get_int_value('gene_count')
            if gene_count is not None:
                defaults['gene_count'] = gene_count
            
            genome_size = get_float_value('genome_size')
            if genome_size is not None:
                defaults['genome_size'] = round(genome_size, 2)
            
            busco = get_decimal_value('busco')
            if busco is not None:
                defaults['busco'] = busco
            
            # 检查是否有有效数据（至少要有中文名）
            if not defaults['name_cn']:
                print(f"⚠️  跳过 taxonomy_id={tax_id}: 缺少中文名")
                skipped_count += 1
                continue
            
            # 更新或创建
            obj, created = Species.objects.update_or_create(
                taxonomy_id=tax_id,
                defaults=defaults
            )
            
            if created:
                created_count += 1
                print(f"  ✅ 新增物种: {obj.name_cn} (ID: {tax_id})")
            else:
                updated_count += 1
                if updated_count <= 5:  # 只打印前5条更新记录
                    print(f"  📝 更新物种: {obj.name_cn} (ID: {tax_id})")
                
        except Exception as e:
            error_count += 1
            tax_id = row.get('taxonomy_id', 'Unknown')
            print(f"❌ 处理 taxonomy_id={tax_id} 时出错: {e}")
            continue
    
    # 打印最终统计
    print(f"\n{'='*50}")
    print(f"✅ 物种更新完成！")
    print(f"{'='*50}")
    print(f"📊 统计信息:")
    print(f"  - 新增物种: {created_count} 条")
    print(f"  - 更新物种: {updated_count} 条")
    print(f"  - 跳过记录: {skipped_count} 条")
    print(f"  - 错误记录: {error_count} 条")
    print(f"  - 总计处理: {len(df)} 条")
    print(f"{'='*50}")

if __name__ == "__main__":
    print("========== 开始导入物种 ==========")
    update_all_species()
