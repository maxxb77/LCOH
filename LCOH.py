import pandas as pd
import os

cur_dir = os.path.dirname(os.path.realpath(__file__))
outname = 'v1.csv'


# Example DataFrame
df = pd.read_csv(os.path.join(cur_dir,"lcoh_pieces_3.csv"))
version = pd.read_csv(os.path.join(cur_dir,"version.csv"))
result= pd.DataFrame(columns=list(df.columns) + ['version_name'])
for j in range(len(version)):
    df_2=df.copy()
    df_2['version_name']=version.iloc[j, 0]
    df_2.loc[df_2['lcoh_cat'] == 'fom', 'LCOH($/kg)'] *= version['fom'][j]*1000
    df_2.loc[df_2['lcoh_cat'] == 'capcost', 'LCOH($/kg)'] *= version['capcost'][j]*1000
    df_2.loc[df_2['lcoh_cat'] == 'electricity-grid-retailer', 'LCOH($/kg)'] *= version['electricity-grid-retailer'][j]
    result = pd.concat([result, df_2], ignore_index=True)
 
result.to_csv(os.path.join(cur_dir,outname))