import pandas as pd
import os
import sys

species = ['Anethum.graveolens', 'Carum.carvi', 'Changium.smyrnioides', 'Cicuta.virosa', 'Cnidium.monnieri',
           'Conium.maculatum', 'Dickinsia.hydrocotyloides', 'Ferula.sinkiangensis', 'Glehnia.littoralis',
           'Ligusticum.sinense', 'Oenanthe.javanica', 'Pastinaca.sativa']
file1 = sys.argv[1]   # loc file
file2 = sys.argv[2]   # pfam file
file3 = sys.argv[3]   # nr file
file4 = sys.argv[4]   # swissprot file
file5 = sys.argv[5]   # go_ec_kegg_pathway file
output = sys.argv[6]  # output file

df1 = pd.read_table(file1, header=['chr', 'start', 'end', 'stand', 'gene'], sep='\t')
print(df1.head)
df2 = pd.read_table(file2, header=['gene', 'pfam'])
df3 = pd.read_table(file3, header=['gene', 'nr'])
df4 = pd.read_table(file4, header=['gene', 'swissprot'])
df5 = pd.read_table(file5, header=['gene', 'go', 'ec', 'ko', 'map'])


merge_file1 = pd.merge(df1, df2, how='outer', on='gene')
merge_file2 = pd.merge(merge_file1, df3, how='outer', on='gene')
merge_file3 = pd.merge(merge_file2, df4, how='outer', on='gene')
merge_file = pd.merge(merge_file3, df5, how='outer', on='gene')

merge_file.to_sql()
merge_file.to_csv(output, index=None)