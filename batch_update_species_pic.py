#!/usr/bin/env python3
"""
批量更新Species模型的species_pic_path字段
从CSV文件读取name_latin和species_pic_path，匹配数据库中的物种并更新
"""
import os
import sys
import csv
import logging

# 将Django项目根目录加入Python路径（关键：让脚本能导入Django模型）
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apiaceae.settings')  # 替换为你的项目settings模块名

# 初始化Django
import django
django.setup()

# 导入Species模型
from home.models import Species

# 配置日志（方便查看导入结果）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_update_pic.log'),  # 日志写入文件
        logging.StreamHandler(sys.stdout)  # 同时输出到控制台
    ]
)
logger = logging.getLogger(__name__)

def batch_update_species_pic(csv_path):
    """
    批量更新物种图片路径
    :param csv_path: CSV文件路径
    """
    # 统计变量
    total_count = 0  # 总记录数
    success_count = 0  # 成功更新数
    fail_count = 0  # 失败数
    not_found_count = 0  # 未找到物种数
    fail_records = []  # 失败记录

    # 检查CSV文件是否存在
    if not os.path.exists(csv_path):
        logger.error(f"CSV文件不存在：{csv_path}")
        return

    # 读取CSV文件并循环处理
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            # 用DictReader读取，按列名取值（需确保CSV有name_latin和species_pic_path列）
            reader = csv.DictReader(f)
            
            # 验证CSV列名是否正确
            required_columns = {'name_latin', 'species_pic_path'}
            if not required_columns.issubset(reader.fieldnames):
                missing_cols = required_columns - set(reader.fieldnames)
                logger.error(f"CSV文件缺少必要列：{missing_cols}，请检查列名")
                return

            # 循环处理每一行
            for row in reader:
                total_count += 1
                name_latin = row.get('name_latin', '').strip()
                pic_path = row.get('species_pic_path', '').strip()

                # 跳过空的拉丁名
                if not name_latin:
                    logger.warning(f"第{total_count}行：拉丁名为空，跳过")
                    fail_count += 1
                    fail_records.append(f"第{total_count}行：拉丁名为空")
                    continue

                try:
                    # 查询匹配的物种（严格匹配name_latin）
                    species = Species.objects.get(name_latin=name_latin)
                    
                    # 仅当路径有变化时才更新（避免无意义的数据库操作）
                    if species.species_pic_path != pic_path:
                        species.species_pic_path = pic_path
                        species.save()
                        success_count += 1
                        logger.info(f"成功更新：{name_latin} -> 图片路径：{pic_path}")
                    else:
                        success_count += 1
                        logger.info(f"无需更新：{name_latin}（路径未变化）")

                except Species.DoesNotExist:
                    # 未找到对应物种
                    not_found_count += 1
                    fail_count += 1
                    fail_records.append(f"第{total_count}行：{name_latin} - 数据库中未找到该物种")
                    logger.warning(f"未找到物种：{name_latin}")
                except Exception as e:
                    # 其他异常
                    fail_count += 1
                    fail_records.append(f"第{total_count}行：{name_latin} - 错误：{str(e)}")
                    logger.error(f"更新失败：{name_latin} - 错误：{str(e)}")

    except Exception as e:
        logger.error(f"读取CSV文件出错：{str(e)}")
        return

    # 输出汇总结果
    logger.info("="*50)
    logger.info(f"批量更新完成！汇总结果：")
    logger.info(f"总记录数：{total_count}")
    logger.info(f"成功更新数：{success_count}")
    logger.info(f"失败数：{fail_count}")
    logger.info(f"未找到物种数：{not_found_count}")
    
    if fail_records:
        logger.info(f"失败记录详情：")
        for record in fail_records:
            logger.info(f"  - {record}")
    logger.info("="*50)

if __name__ == '__main__':
    # CSV文件路径（根据你的实际路径修改）
    csv_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'home/static/home/plugins/files/species.csv'
    )
    
    # 执行批量更新
    batch_update_species_pic(csv_file_path)
