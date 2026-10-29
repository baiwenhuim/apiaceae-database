# from ..models import Gene
import pandas as pd
from django.conf import settings
from sqlalchemy import create_engine
import glob

scientific_species = ["Anethum.graveolens", "Angelica.biserrata", "Angelica.dahurica", "Angelica.keiskei", "Angelica.sinensis",
        "Apium.graveolens", "Bupleurum.chinense", "Carum.carvi", "Centella.asiatica", "Changium.smyrnioides", "Cicuta.virosa",
        "Cnidium.monnieri", "Conium.maculatum", "Coriandrum.sativum", "Daucus.carota", "Dickinsia.hydrocotyloides",
        "Ferula.sinkiangensis", "Glehnia.littoralis", "Heracleum.sosnowskyi", "Ligusticum.chuanxiong.hapA",
        "Ligusticum.chuanxiong.hapB", "Ligusticum.sinense", "Notopterygium.incisum", "Oenanthe.javanica",
        "Pastinaca.sativa", "Petroselinum.crispum.var.crispum", "Petroselinum.crispum.var.neapolitanum",
        "Peucedanum.praeruptorum", "Sanicula.chinensis", "Saposhnibopia.divaricata"]
normal_species_name = ['shiluo', 'duhuo', 'baizhi', 'mingriye', 'danggui', 'qincai', 'beicaihu', 'gelvzi', 'jixuecao',
        'mingdangsen', 'duqin', 'shechuangzi', 'dusen', 'xiangcai', 'carrot', 'matiqin', 'awei', 'shanhucai', 'tianhusui',
        'oudanggui', 'chuangxionghapA', 'chuangxionghapB', 'gaoben', 'qianghuo', 'shuiqin', 'oufangfen', 'pinyeouqin',
        'zhouyeouqin', 'qianhu', 'biandoucai', 'fangfen']
tuple_species = tuple(zip(normal_species_name, scientific_species))
'''
This script aim to import gene location and function from csv file to mysql database
Currently, it is only import one file (means one species)--- 27/8/2024
Next step, added iterate for all species;
'''

# Configure Django settings before accessing them
settings.configure()

# Step 2: Create a SQLAlchemy engine to connect to the MySQL database
#driver = settings.DATABASES['default']['ENGINE']   # they all get error "KeyError: 'default'", I don't know why!
# user = settings.DATABASES['default']['USER']     
# password = settings.DATABASES['default']['PASSWORD']
# database_name = settings.DATABASES['default']['NAME']
# host = settings.DATABASES['default']['HOST']
# port = settings.DATABASES['default']['PORT']

database_url = 'mysql://{user}:{password}@localhost:3306/{database_name}'.format(
    # driver = 'django.db.backends.mysql',
    user='baiwenhui',
    password='Baiwenhui.0121',
    database_name='apiaceae',
)

engine = create_engine(database_url, echo=False)

def gene_data():
    # Step 1: Create a DataFrame with the data
    file_path = '/mnt/d/Coding/Web/apiaceae/home/static/home/plugins/files/gene_function/Anethum.graveolens.csv'
    assemably_file = pd.read_csv(file_path, header=0)

    # Step 3: Convert the Pandas DataFrame to a format for MySQL table insertion
    assemably_file.to_sql('home_gene', con=engine, if_exists='replace', index=False)
    print('finish', file_path)

# gene_data()

def shiluo():
    # Step 1: Create a DataFrame with the data
    file_path = '/mnt/e/backup/static/home/plugins/files/transcriptome/transcriptome/Anethum.graveolens.gene_exp.tpm.txt'
    df = pd.read_table(file_path, header=0)
    df['root'] = df.iloc[:, 1:4].mean(axis=1)
    df['stem'] = df.iloc[:, 4:7].mean(axis=1)
    df['leaf'] = df.iloc[:, 7:10].mean(axis=1)
    df['gene_id'] = df['Gene ID']
    new_data = df[['gene_id', 'root', 'stem', 'leaf']]
    # Step 3: Convert the Pandas DataFrame to a format for MySQL table insertion
    new_data.to_sql('shiluo', con=engine, if_exists='replace', index=False)
    print('finish', file_path)

shiluo()

def expression_data():
    path = '/mnt/d/Coding/Web/apiaceae/home/static/home/plugins/files/transcriptome/transcriptome/'
    txt_files = glob.glob(path + "*.txt")
    for file_path in txt_files:
        if tuple_species[2][1] in file_path:
            df = pd.read_table(file_path, header=0)
            df['root'] = df.iloc[:, 1:4].mean(axis=1)
            df['root1'] = df.iloc[:, 4:7].mean(axis=1)
            df['root2'] = df.iloc[:, 7:10].mean(axis=1)
            df['root3'] = df.iloc[:, 10:13].mean(axis=1)
            df['root4'] = df.iloc[:, 13:16].mean(axis=1)
            df['root5'] = df.iloc[:, 16:19].mean(axis=1)
            df['root6'] = df.iloc[:, 19:22].mean(axis=1)
            df['flower'] = df.iloc[:, 22:25].mean(axis=1)
            # df['petiole'] = df.iloc[:, 25:28].mean(axis=1)     
            df['stem'] = df.iloc[:, 28:31].mean(axis=1)
            df['old_leaf'] = df.iloc[:, 31:34].mean(axis=1)
            df['young_leaf'] = df.iloc[:, 34:37].mean(axis=1)
            # df['leaf'] = df.iloc[:, 7:10].mean(axis=1)
            df['gene_id'] = df['Gene ID']
            new_data = df[['gene_id', 'root', 'root1', 'root2', 'root4', 'root5', 'root6', 'flower', 'stem','old_leaf','young_leaf']]   # the columns of dataframe must same with fields of model
            new_data.to_sql(tuple_species[2][0], con=engine, if_exists='replace', index=False)
            file_name = tuple_species[2][0] + '.csv'
            new_data.to_csv(file_name)
            print('process', tuple_species[2][0])

# expression_data()

# Ref: https://github.com/chrisdev/django-pandas/issues/125
def to_django(df, DjangoModel, if_exists="fail"):
    """Uses bulk_create to insert data to Django table
    if_exists: see pd.DataFrame.to_sql API

    Ref: https://www.webforefront.com/django/multiplemodelrecords.html
    """
    import numpy as np

    if if_exists not in ["fail", "replace", "append"]:
        raise Exception("if_exists must be fail, replace or append")

    if if_exists == "replace":
        DjangoModel.objects.all().delete()
    elif if_exists == "fail":
        if DjangoModel.objects.all().count() > 0:
            raise ValueError("Data already exists in this table")
    else:
        pass

    dct = df.replace({np.nan: None}).to_dict(
        "records"
    )  # replace NaN with None since Django doesn't understand NaN

    bulk_list = []
    for x in dct:
        bulk_list.append(DjangoModel(**x))
    DjangoModel.objects.bulk_create(bulk_list)
    print("Successfully saved DataFrame to Django table.")

def check_dataframe_columns(
    df: pd.DataFrame, DjangoModel: Type[models.Model], strict: bool = False
):
    """Raises KeyError if DataFrame doesn't match a Django model

    Parameters
    ----------
    df: A pandas DataFrame object
    DjangoModel: A Django model
    strict: If strict is True, then the DataFrame must contain the exact set of columns
        as the Django mode
    """
    # todo: add column type checking
    error_list = []
    dataframe_columns = set(df.columns)
    django_columns = set(map(lambda x: x.name, DjangoModel._meta.fields))
    if not dataframe_columns.issubset(django_columns):
        unknown_columns = list(dataframe_columns - django_columns)
        unknown_columns.sort()  # to be repeatable
        error_list.append(
            f"DataFrame contains unknown column(s): {', '.join(unknown_columns)}"
        )
    if strict and not dataframe_columns == django_columns:
        missing_columns = list(django_columns - dataframe_columns)
        missing_columns.sort()  # to be repeatable
        error_list.append(
            f"With strict=True, DataFrame is missing column(s): {', '.join(missing_columns)}"
        )

    if error_list:
        raise KeyError(" | ".join(error_list))