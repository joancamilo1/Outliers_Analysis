# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 08:14:34 2024

@author: joan camilo tamayo

analisis de cups

1. concatenate 2 tables: HUDN + LCCR, columns: Periodo, CUPS, Descripción CUPS, Valor Unitario 
2. after union, filter cups located in: CUPS Cirugia 
3. remove outliers 
"""
import pandas as pd

LCCR = pd.read_excel(r"D:\Users\WS-012\Desktop\Outliders\in\VENTA-COSTOS UNITARIOS CX LCCR.xlsx", engine='openpyxl', sheet_name='default_1', dtype=str) 
HUDN = pd.read_excel(r"D:\Users\WS-012\Desktop\Outliders\in\VENTAS UNITARIAS CX HUDN 1.xlsx", engine='openpyxl', sheet_name='default_1', dtype=str) 

CUPS = pd.read_excel(r"D:\Users\WS-012\Desktop\Outliders\in\CUPS Cirugia.xls",sheet_name='CUPS x Especialidad',  dtype=str) 

LCCR.columns
HUDN.columns

#--------------------- concatenate LCCR and HUDN -----------------------------
# Extract Cups description
LCCR['DESC_CUPS'] = LCCR['CUPS'].str.split('-', expand=True)[1].str.strip()

# column filters
# PERIODO,  DIM_INGRESO, 	 ID_CUPS, 	 CUPS ,COSTO_UNITARIO
LCCR = LCCR[['PERIODO','ID_CUPS','DESC_CUPS' ,'COSTO_UNITARIO', 'VENTA UNITARIA']] 

# Column renamers
LCCR.rename(columns={'VENTA UNITARIA': 'VENTA_UNITARIA'}, inplace=True)

HUDN = HUDN[['PERIODO','DIM_COD_SERVICIO','DIM_DESC_SERVICIO' ,'DIM_VALOR_UNITARIO', 'COSTO_UNITARIO']] 

New_names ={'PERIODO': 'PERIODO',
            'DIM_COD_SERVICIO': 'ID_CUPS',
            'DIM_DESC_SERVICIO': 'DESC_CUPS',
            'DIM_VALOR_UNITARIO': 'VENTA_UNITARIA',
            'COSTO_UNITARIO': 'COSTO_UNITARIO'
            }
HUDN.rename(columns=New_names, inplace=True) #--------------------------------------- falta COSTO_UNITARIO

# Concatenated data
Ventas = pd.concat([LCCR, HUDN])
Ventas = Ventas.dropna() # drop blank records  

Ventas['VENTA_UNITARIA'] = Ventas['VENTA_UNITARIA'].astype(float).astype(int)

Ventas = Ventas[~Ventas['COSTO_UNITARIO'].str.contains('-')] # delete negative data
Ventas['COSTO_UNITARIO'] = Ventas['COSTO_UNITARIO'].astype(float).astype(int)


#--------------------- Prepare table of cups to filter -----------------------
CUPS = CUPS.dropna() # drop blank records  

CUPS.columns = CUPS.iloc[0] # first row as header 
CUPS = CUPS[1:]
CUPS.columns

CUPS = CUPS[['CUPS RES. 2557']] # column filter and rename
CUPS.rename(columns={'CUPS RES. 2557': 'ID_CUPS'}, inplace=True)

# Filter cups in ventas that r in CUPS
Ventas_Costos_filtradas = Ventas[Ventas['ID_CUPS'].isin(CUPS['ID_CUPS'])]

Ventas_Costos_filtradas.columns

Ventas_Costos_filtradas = Ventas_Costos_filtradas[Ventas_Costos_filtradas['VENTA_UNITARIA'] > 100] 
Ventas_Costos_filtradas = Ventas_Costos_filtradas[Ventas_Costos_filtradas['COSTO_UNITARIO'] > 100] 


# numero de repeticiones de un valor por cup
# Ventas_Costos_filtradas_prueba = Ventas_Costos_filtradas
# Ventas_Costos_filtradas_prueba['Recuento_Venta_Unitaria'] = Ventas_Costos_filtradas.groupby(['ID_CUPS', 'VENTA_UNITARIA'])['VENTA_UNITARIA'].transform('count')


#--------------------- Outlider analysis  ------------------------------------
# outlider visualization
import seaborn as sns
import matplotlib.pyplot as plt

# Boxplot by group
# ------------------- VENTA_UNITARIA ------------------
plt.figure(figsize=(160, 80))
sns.boxplot(data=Ventas_Costos_filtradas, x='ID_CUPS', y='VENTA_UNITARIA')
plt.title('Boxplot of VENTA_UNITARIA by ID_CUPS')
plt.xticks(rotation=45)
plt.show()

# ------------------- VENTA_UNITARIA ------------------
plt.figure(figsize=(160, 80))
sns.boxplot(data=Ventas_Costos_filtradas, x='ID_CUPS', y='COSTO_UNITARIO')
plt.title('Boxplot of COSTO_UNITARIO by ID_CUPS')
plt.xticks(rotation=45)
plt.show()


# ------------------- IQR Analysis ------------------
# https://www.scribbr.com/statistics/interquartile-range/

# ------------------- VENTA_UNITARIA ------------------
Ventas_Q1 = Ventas_Costos_filtradas.groupby('ID_CUPS')['VENTA_UNITARIA'].quantile(0.25) # Calculate the value of the first quartile (Q1)
Ventas_Q3 = Ventas_Costos_filtradas.groupby('ID_CUPS')['VENTA_UNITARIA'].quantile(0.75) # Calculate the value of the third quartile (Q3)
Ventas_IQR = Ventas_Q3 - Ventas_Q1 # Calculate the interquartile range (IQR)

# define limits to identify outliers
Ventas_limite_inferior = Ventas_Q1 - 1.5 * Ventas_IQR
Ventas_limite_superior = Ventas_Q3 + 1.5 * Ventas_IQR

# remove outliers from Ventas_Costos_filtradas
Ventas_filtrados = Ventas_Costos_filtradas.groupby('ID_CUPS').apply(lambda x: x[(x['VENTA_UNITARIA'] >= Ventas_limite_inferior[x.name]) & 
                                                                  (x['VENTA_UNITARIA'] <= Ventas_limite_superior[x.name])])

Ventas_sin_outliers = Ventas_filtrados.reset_index(drop=True) # Rebuild the df without outliers

Ventas_sin_outliers['Lim_Inf_VENTA_UNITARIA'] = Ventas_sin_outliers.groupby('ID_CUPS')['VENTA_UNITARIA'].transform(lambda x: max(x.quantile(0.25) - 1.5 * (x.quantile(0.75) - x.quantile(0.25)), x.min()))
Ventas_sin_outliers['Lim_Sup_VENTA_UNITARIA'] = Ventas_sin_outliers.groupby('ID_CUPS')['VENTA_UNITARIA'].transform(lambda x: x.quantile(0.75) + 1.5 * (x.quantile(0.75) - x.quantile(0.25)))
Ventas_sin_outliers['Media_VENTA_UNITARIA'] = Ventas_sin_outliers.groupby('ID_CUPS')['VENTA_UNITARIA'].transform('mean')


# ------------------- COSTO_UNITARIO ------------------
COSTO_Q1 = Ventas_Costos_filtradas.groupby('ID_CUPS')['COSTO_UNITARIO'].quantile(0.25) # Calculate the value of the first quartile (Q1)
COSTO_Q3 = Ventas_Costos_filtradas.groupby('ID_CUPS')['COSTO_UNITARIO'].quantile(0.75) # Calculate the value of the third quartile (Q3)
COSTO_IQR = COSTO_Q3 - COSTO_Q1 # Calculate the interquartile range (IQR)

# define limits to identify outliers
COSTO_limite_inferior = COSTO_Q1 - 1.5 * COSTO_IQR
COSTO_limite_superior = COSTO_Q3 + 1.5 * COSTO_IQR

# remove outliers from Ventas_Costos_filtradas
COSTO_filtrados = Ventas_Costos_filtradas.groupby('ID_CUPS').apply(lambda x: x[(x['COSTO_UNITARIO'] >= COSTO_limite_inferior[x.name]) & 
                                                                  (x['COSTO_UNITARIO'] <= COSTO_limite_superior[x.name])])

COSTO_sin_outliers = COSTO_filtrados.reset_index(drop=True) # Rebuild the df without outliers

COSTO_sin_outliers['Lim_Inf_COSTO_UNITARIO'] = COSTO_sin_outliers.groupby('ID_CUPS')['COSTO_UNITARIO'].transform(lambda x: max(x.quantile(0.25) - 1.5 * (x.quantile(0.75) - x.quantile(0.25)), x.min()))
COSTO_sin_outliers['Lim_Sup_COSTO_UNITARIO'] = COSTO_sin_outliers.groupby('ID_CUPS')['COSTO_UNITARIO'].transform(lambda x: x.quantile(0.75) + 1.5 * (x.quantile(0.75) - x.quantile(0.25)))
COSTO_sin_outliers['Media_COSTO_UNITARIO'] = COSTO_sin_outliers.groupby('ID_CUPS')['COSTO_UNITARIO'].transform('mean')


#-----------------  union ------------------------------
Ventas_sin_outliers.columns
COSTO_sin_outliers.columns

# Unir los DataFrames utilizando el método merge
merged_df = Ventas_sin_outliers.merge(COSTO_sin_outliers, on=['PERIODO', 'ID_CUPS', 'DESC_CUPS',
                                                              'COSTO_UNITARIO', 'VENTA_UNITARIA'], how='outer')
# Eliminar filas con datos en blanco
merged_df = merged_df.dropna()
# Eliminar registros duplicados
merged_df = merged_df.drop_duplicates()


# Reordenar las columnas en el orden deseado
column_order = ['PERIODO', 'ID_CUPS', 'DESC_CUPS', 
                'COSTO_UNITARIO', 'Lim_Inf_COSTO_UNITARIO', 'Lim_Sup_COSTO_UNITARIO', 'Media_COSTO_UNITARIO',
                'VENTA_UNITARIA', 'Lim_Inf_VENTA_UNITARIA', 'Lim_Sup_VENTA_UNITARIA', 'Media_VENTA_UNITARIA'
                ]
Ventas_Costos_sin_outliers = merged_df[column_order]

DATA_INT = ['COSTO_UNITARIO', 'Lim_Inf_COSTO_UNITARIO', 
            'Lim_Sup_COSTO_UNITARIO', 'Media_COSTO_UNITARIO',
            'VENTA_UNITARIA', 'Lim_Inf_VENTA_UNITARIA', 
            'Lim_Sup_VENTA_UNITARIA', 'Media_VENTA_UNITARIA']

Ventas_Costos_sin_outliers[DATA_INT] = Ventas_Costos_sin_outliers[DATA_INT].astype(float).astype(int)


# save outliers from Ventas_Costos_filtradas
outliers = Ventas_Costos_filtradas.merge(merged_df, indicator=True, how='outer').loc[lambda x: x['_merge'] == 'left_only']
Ventas_Costos_outliers = outliers.drop('_merge', axis=1) # remove temporary column _merge 
Ventas_Costos_outliers = Ventas_Costos_outliers.dropna(axis=1)


# se requiere tambien el archivo unicamente con los limites y valor medio de costo y venta para cada cup 
Ventas_Costos_sin_outliers.columns 
filtro_final = ['ID_CUPS', 'DESC_CUPS', 
                'Lim_Inf_COSTO_UNITARIO', 'Lim_Sup_COSTO_UNITARIO','Media_COSTO_UNITARIO',
                'Lim_Inf_VENTA_UNITARIA','Lim_Sup_VENTA_UNITARIA', 'Media_VENTA_UNITARIA']
Ventas_Costos_sin_outliers_cup_unico = Ventas_Costos_sin_outliers[filtro_final] 
Ventas_Costos_sin_outliers_cup_unico = Ventas_Costos_sin_outliers_cup_unico.drop_duplicates()



# =============================== OUT DATA ====================================
Ventas.to_excel(r"D:\Users\WS-012\Desktop\Outliders\out\1.LCCR_HUDN_Concatenadas.xlsx", index=False)
Ventas_Costos_filtradas.to_excel(r"D:\Users\WS-012\Desktop\Outliders\out\2.Ventas_Costos_CUPs_filtradas.xlsx", index=False)
Ventas_sin_outliers.to_excel(r"D:\Users\WS-012\Desktop\Outliders\out\3A.Ventas_sin_outliers.xlsx", index=False)
COSTO_sin_outliers.to_excel(r"D:\Users\WS-012\Desktop\Outliders\out\3B.COSTO_sin_outliers.xlsx", index=False)
Ventas_Costos_outliers.to_excel(r"D:\Users\WS-012\Desktop\Outliders\out\3C.Ventas_outliers.xlsx", index=False)

Ventas_Costos_sin_outliers.to_excel(r"D:\Users\WS-012\Desktop\Outliders\out\4.Ventas_Costos_sin_outliers.xlsx", index=False)
Ventas_Costos_sin_outliers_cup_unico.to_excel(r"D:\Users\WS-012\Desktop\Outliders\out\5.Ventas_Costos_sin_outliers_cup_unico.xlsx", index=False)

