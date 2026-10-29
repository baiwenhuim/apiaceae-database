from home.models import Species
from django.core.cache import cache

def species_name(request):
    # 先查缓存，缓存不存在再查数据库
    species_list = cache.get('species_name_list')
    if not species_list:
        species_list = Species.objects.filter(
            name_latin__isnull=False
        ).exclude(
            name_latin=''
        ).values_list('name_latin', flat=True).order_by('name_latin')
        # 缓存1小时（3600秒），避免频繁查库
        cache.set('species_name_list', species_list, 3600)
    
    return {
        'species_name': species_list,
    }

# 还可以在这个文件/文件夹中添加更多处理器
def site_info(request):
    """示例：存放网站标题、版权等全局信息"""
    return {
        'site_title': '伞形科数据库',
        'copyright': '© 2026 Apiaceae Database'
    }