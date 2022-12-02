# -*- coding: utf-8 -*-
"""CRM1

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/16gJ694On4E1TWjmW3rT6yA8O0ee3g3Eh
"""

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import numpy as np
import pandas as pd
from ast import literal_eval
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

pd.set_option('display.float_format', lambda x: '%.2e' % x)
pd.options.mode.chained_assignment = None  # default='warn'


def read_adas4(adas4_file, add_process_type, ):
  with open(adas4_file) as file:
    array = [row.strip() for row in file]
  line_num = []
  for i in range(len(array)):
    if array[i] == '-1':
      line_num.append(i)
  #read configuration data, energy cm-1
  z1 = [i.split()[:] for i in array[(2):line_num[0]]]
  df1 = pd.DataFrame(z1[:])
  l = []
  for i in range(len(z1)):
    l.append(str(z1[i][3]+z1[i][4]))
  df1[7] = l
  df1 = df1.drop({1,3,4,6}, axis=1)
  df2 = pd.DataFrame(data = {'Level_i': ['1'],  'Configuration': ['1s1'] , 'Energy': ['0'], '(2S+1)L(J)': ['(1)0(0.0)']}) #data for i = 1
  df1 = df1.rename(columns={0: 'Level_i', 2: 'Configuration', 5: 'Energy', 7: '(2S+1)L(J)'})
  df_conf = pd.concat([df2, df1]).reset_index().drop(['index'], axis=1) # got config dataset
  df_conf['Energy'] = df_conf['Energy'].astype(float)
  df_conf['Energy_eV'] = [i*h*c for i in df_conf.Energy[:]] #transfering energy to eV
  #df_conf = df_conf.drop(['Energy'], axis=1)
  df_conf['Configuration'] = df_conf['Configuration'].str.lower()
 
  J_list = []
  degen = []
  for i in df_conf['(2S+1)L(J)']:
    symb = []
    for j in range(len(i)):
      if i[j] == '(':
        symb.append(j)
    J_list.append(float(i[symb[1]+1:-1]))
    degen.append(2*float(i[symb[1]+1:-1])+1) #2J+1 https://mipt.ru/dmcp/student/sc_work/Kostykevich_220508.pdf
  df_conf['degeneracy'] = degen
  df_conf['J'] = J_list

  #read coef data
  z = [i.split()[:] for i in array[(line_num[0]+2):line_num[1]]] 
  for i in range(len(z)):
    for j in range(len(z[i])):
      if z[i][j] != '+1':
        if '+' in z[i][j]:
          z[i][j] = z[i][j].replace('+', 'e+')
        elif '-' in z[i][j]:
          z[i][j] = z[i][j].replace('-', 'e-')
  df = pd.DataFrame(z[:])

  #print(nums_from_string.get_nums(array[(line_num[0]+1)]))
 # check process reading
  df_pr = df.loc[df[0] == add_process_type]
  df = df.loc[df[0] != add_process_type]
  if add_process_type == 'S':
    df = df.drop([17], axis = 1)
  '''cols = ['Level_j', 'Level_i', 'A3', '5.00+02', '1.00+03', '2.00+03', '3.00+03', '5.00+03',
          '1.00+04', '1.50+04', '2.00+04', '3.00+04', '5.00+04', '1.00+05',
          '1.50+05', '2.00+05', '5.00+05']'''
  cols = ['Level_j', 'Level_i', 'A3', '1.16+04', '2.32+04', '5.80+04', '1.16+05',
        '2.32+05', '5.80+05', '1.16+06', '2.32+06', '5.80+06', '1.16+07',
        '2.32+07', '5.80+07', '1.16+08', '2.32+08'] # helike_hps02he
  
  eV = 8.61732814974056E-05
  l = ['Level_j', 'Level_i', 'A3']
  for i in cols:
      if '+' in i:
          l.append(str(round(literal_eval(str(i).replace('+', 'e+'))*eV,6)))
  for i in range(len(l)):
      df = df.rename(columns={i : l[i]})
  df.iloc[:,2:] = df.iloc[:,2:].astype(float)
   
  df_pr = df_pr.rename(columns={0:'pr_type'})
  Aki_adas = df[{'Level_j', 'Level_i', 'A3'}]
  df = df.drop(['A3'], axis=1)
  l.remove('A3')
  if add_process_type == 'S':
    df_pr = df_pr.drop(2, axis = 1)
    
  for i in range(len(l)):
    df_pr = df_pr.rename(columns={df_pr.columns[i+1]: l[i]})
  df_pr = df_pr.drop(['Level_i'], axis=1)
  df_pr = df_pr.rename(columns={'Level_j': 'Level_i'})
  '''if add_process_type == 'S':
    df_pr = df_pr.drop(['A3'], axis=1)'''
  df_pr.iloc[:,2:] = df_pr.iloc[:,2:].astype(float)

  return df, df_pr, df_conf, Aki_adas

def adas_Aij(Aki_adas, lvl_i):
    l = []
    for i in list(range(1, 20)):
      if str(i) not in list(Aki_adas.Level_j.loc[Aki_adas.Level_i == lvl_i]) and i != int(lvl_i):
        l.append(str(i))

    s = pd.DataFrame()
    s['A3'] = [1e-30]* len(l)

    s['Level_j'] = l
    s['Level_i'] = lvl_i
    Aji = pd.concat([Aki_adas.loc[Aki_adas.Level_i == lvl_i], s], axis = 0)
    Aji.Level_j=Aji.Level_j.astype(int)
    Aji = Aji.sort_values('Level_j').reset_index(drop=True)
    Aji.Level_j=Aji.Level_j.astype(str)
    
    return Aji

def interp_coef(Te_val, temperature_range, df_to_interp):
  l = []
  for i in df_to_interp.index:    
    f1 = interp1d(temperature_range, df_to_interp[df_to_interp.columns[2:]].iloc[df_to_interp.index == i], kind='linear')
    l.append(float(f1(Te_val)))
  return l

def coef_calc(df_ex, df_config, df_r, df_i, Te1, lvl_i):
    Te_range = [float(j) for j in df_ex.columns[2:]]
    if float(Te1) not in Te_range:
        df_ex[Te1] = interp_coef(Te1, Te_range, df_ex)
    Yij = df_ex[{'Level_i', 'Level_j', Te1}].loc[(df_ex.Level_i == lvl_i) | (df_ex.Level_j == lvl_i)].reset_index(drop=True)
    
    
    dE = (df_config['Energy_eV'].loc[df_config['Level_i'] != lvl_i] - float(
        df_config['Energy_eV'].loc[df_config['Level_i'] == lvl_i])).reset_index(drop=True)
    #print(dE)
    
    wi = float(df_config['degeneracy'].loc[df_config['Level_i'] == lvl_i])
    wj = df_config['degeneracy'].loc[df_config['Level_i'] != lvl_i].reset_index(drop=True)
    Y = Yij[Te1].reset_index(drop=True)
    
    qij = const / wi * (IH/float(Te1))**0.5 * np.exp(-dE/float(Te1)) * Y
    
    qji = wi / wj * np.exp(-dE/float(Te1)) * qij
    df_coef = pd.DataFrame(data = Yij[{'Level_j', 'Level_i'}])
    
    #df_coef['qij'] = qij
    #df_coef['qji'] = qji
    
    df_coef['qij'] = pd.concat([qji[:int(lvl_i)-1], qij[int(lvl_i)-1:]], axis=0)
    df_coef['qji'] = pd.concat([qij[:int(lvl_i)-1], 
                    qji[int(lvl_i)-1:]], axis=0)
    
    df_r[Te1] = interp_coef(Te1, Te_range, df_r)
    df_i[Te1] = interp_coef(Te1, Te_range, df_i)
    
    rec_coef_df, ion_coef_df = df_r[{'Level_i'	, Te1}], df_i[{'Level_i', Te1}]
    #Si = float(ion_coef_df[Te1].loc[ion_coef_df.Level_i==lvl_i])
    Si = float(ion_coef_df[Te1].loc[ion_coef_df.Level_i==lvl_i])  / np.exp((ion_potential - float(
        df_config['Energy_eV'].loc[df_config['Level_i'] == lvl_i]))/float(Te1))
    R = float(rec_coef_df[Te1].loc[rec_coef_df.Level_i==lvl_i])
    
    df_coef['Si'] = Si
    df_coef['R'] = R
    #print(qji)
    return df_coef


def matrix_cols_calc(ne, df_coef, Aji_full, lvl_i):
    m_Aij = Aji_full.loc[Aji_full.Level_j == lvl_i].reset_index(drop=True)
    m_Aji = Aji_full.loc[Aji_full.Level_i == lvl_i].reset_index(drop=True)
    
    Cii = -sum(ne*df_coef['Si']/18 + ne*df_coef['qij'] + m_Aij.A3)
    Cij =  m_Aji.A3 + ne*df_coef['qji']
    C_temp = list(Cij)
    C_temp.insert(int(lvl_i)-1, Cii)
    lvl_vector = pd.DataFrame(data = C_temp, columns = [str('lvl_') + lvl_i])
    return lvl_vector


#constants


e = 4.8e-10
eV = 8.61732814974056E-05
h = 4.135667669e-15 #eV*s
c = 29979245800 #cm/s
const = 2.1716e-8 #cm3 s-1 #for excitation rate coef
IH = 13.6048 #eV
ion_potential = 198310.8 * h * c # cm-1 -> eV

df_ex, df_i, df_config, Aki_adas = read_adas4("helike_hps02he.dat", 'S') 
_, df_r, _, _ = read_adas4("helike_kvi97#he0.dat", 'R')


Te1 = input('Choose temperature in range [0.99961, 19992.201307] eV \n')
ne = float(input('Choose electron density in [0.1, 10]*e+12 cm**-3 \n')) * 1e12  # Electron density in cm**-3


"""
Стационарный случай - 
# 0 = C * n *2..19* + C'
"""
Aji_full = pd.DataFrame()
df_M =  pd.DataFrame()

for i in list(range(1, 20)):
  Aji = adas_Aij(Aki_adas, str(i))
  Aji_full = pd.concat([Aji_full, Aji])

'''
# works for lvl 1
    l = []
    for i in list(range(1, 20)):
      if str(i) not in list(Aki_adas.Level_j.loc[Aki_adas.Level_i == lvl_i]) and i != int(lvl_i):
        l.append(str(i))
'''

Te_range = [float(j) for j in df_ex.columns[2:]]
if float(Te1) not in Te_range:
    df_ex[Te1] = interp_coef(Te1, Te_range, df_ex)


df_coef = pd.DataFrame()
qij_list = []
qji_list = []
for i in list(range(1, 19)):
    lvl_i = str(i)
    Yij = df_ex[{'Level_i', 'Level_j', Te1}].loc[(df_ex.Level_i == lvl_i)].reset_index(drop=True)
    
    lvl_j = list(Yij['Level_j'])
    
    dE = abs(df_config['Energy_eV'].loc[df_config['Level_i'].isin(lvl_j)]- float(
        df_config['Energy_eV'].loc[df_config['Level_i'] == lvl_i])).reset_index(drop=True) 
    
    wi = float(df_config['degeneracy'].loc[df_config['Level_i'] == lvl_i])
    wj = df_config['degeneracy'].loc[df_config['Level_i'].isin(lvl_j)].reset_index(drop=True)
    
    Y = Yij[Te1].reset_index(drop=True)
    
    qij = const / wi * (IH/float(Te1))**0.5 * np.exp(-dE/float(Te1)) * Y
    
    qji = wi / wj * np.exp(-dE/float(Te1)) * qij
    
    #qji = const * 1/wj*(IH/float(Te1))**0.5*Y
    
    df_coef = pd.concat([df_coef, pd.DataFrame(data = Yij[{'Level_j', 'Level_i'}])], axis=0)
    for i in qij.values:
        qij_list.append(float(i))
    for i in qji.values:
        qji_list.append(float(i))  

df_coef['qij'] = qij_list
df_coef['qji'] = qji_list





lvl_i = '5'
Yij = df_ex[{'Level_i', 'Level_j', Te1}].loc[(df_ex.Level_i == lvl_i)].reset_index(drop=True)

lvl_j = list(Yij['Level_j'])

dE = abs(df_config['Energy_eV'].loc[df_config['Level_i'].isin(lvl_j)]- float(
    df_config['Energy_eV'].loc[df_config['Level_i'] == lvl_i])).reset_index(drop=True) 

wi = float(df_config['degeneracy'].loc[df_config['Level_i'] == lvl_i])
wj = df_config['degeneracy'].loc[df_config['Level_i'].isin(lvl_j)].reset_index(drop=True)

Y = Yij[Te1].reset_index(drop=True)

qij = const / wi * (IH/float(Te1))**0.5 * np.exp(-dE/float(Te1)) * Y

qji = wj / wi * np.exp(-dE/float(Te1)) * qij

#qji = const * 1/wj*(IH/float(Te1))**0.5*Y

df_coef = pd.DataFrame(data = Yij[{'Level_j', 'Level_i'}])

df_coef['qij'] = qij
df_coef['qji'] = qji

'''df_coef['qij'] = pd.concat([qji[:int(lvl_i)-1], qij[int(lvl_i)-1:]], axis=0)
df_coef['qji'] = pd.concat([qij[:int(lvl_i)-1], 
                qji[int(lvl_i)-1:]], axis=0)'''









for i in list(range(1, 20)):
  df_coef = coef_calc(df_ex, df_config, df_r, df_i, Te1, str(i))
  '''
  with pd.ExcelWriter('check_coef.xlsx',
                    mode='a') as writer:  
    df_coef.to_excel(writer, sheet_name= str('lvl_' + str(i)))
    '''
  #df_coef.to_excel('check_coef.xlsx')
  df_M[str('lvl_') + str(i)] = matrix_cols_calc(ne, df_coef, Aji_full, str(i))
  
df_M.to_excel('check_matrix.xlsx')

df_M = df_M.drop(0, axis = 0)
C1 = df_M.lvl_1 * (-1)
C = df_M.drop('lvl_1', axis = 1)

x = np.linalg.solve(C, C1) # only sq matrix

print(x)

t = pd.DataFrame(x)

t668 = float(Aji_full.A3.loc[(Aji_full.Level_i == '5')&(Aji_full.Level_j == '10')])
t728 = float(Aji_full.A3.loc[(Aji_full.Level_i == '5')&(Aji_full.Level_j == '7')])
t706 = float(Aji_full.A3.loc[(Aji_full.Level_i == '4')&(Aji_full.Level_j == '6')])   


R_668_728 = t668 * t.iloc[9] / t728 / t.iloc[6]
R_706_728 = t706 * t.iloc[5] / t728 / t.iloc[6]

print(t668 * t.iloc[9] / t728 / t.iloc[6])
print(t706 * t.iloc[5] / t728 / t.iloc[6])


'''
f = open("solved.txt", "w")
f.write('Te \t' + str(Te1) + '\n' )
f.write( 'ne \t' + str(ne) + '\n')
f.write(str(x))
f.write('\n668/728: \t' + str(R_668_728.values[0]) + '\n')
f.write('706/728: \t' + str(R_706_728.values[0]))
f.close()
'''

'''
df_R1 = pd.DataFrame()
df_R2 = pd.DataFrame()

te_range = np.linspace(0.5, 40, 5)
ne_range = np.linspace(1e12, 1e13, 5)
for k in te_range:    
    Te1 = k
    R1 = []
    R2 = []
    for m in ne_range:
        ne = m
        Aji_full = pd.DataFrame()
        df_M =  pd.DataFrame()
        for i in list(range(1, 20)):
          Aji = adas_Aij(Aki_adas, str(i))
          Aji_full = pd.concat([Aji_full, Aji])
        
        for i in list(range(1, 20)):
          qij, qji, Si, R, df_coef = coef_calc(df_ex, df_config, df_r, df_i, Te1, str(i))
          df_M[str('lvl_') + str(i)] = matrix_cols_calc(ne, df_coef, Aji_full, str(i))
    
        df_M = df_M.drop(0, axis = 0)
    
        C1 = df_M.lvl_1 * (-1)
        C = df_M.drop('lvl_1', axis = 1)
    
        x = np.linalg.solve(C, C1) # only sq matrix
    
        print(x)
    
        t = pd.DataFrame(x)

        
        t668 = float(Aji_full.A3.loc[(Aji_full.Level_i == '5')&(Aji_full.Level_j == '10')])
        t728 = float(Aji_full.A3.loc[(Aji_full.Level_i == '5')&(Aji_full.Level_j == '7')])
        t706 = float(Aji_full.A3.loc[(Aji_full.Level_i == '4')&(Aji_full.Level_j == '6')])   
        R_668_728 = t668 * t.iloc[9] / t728 / t.iloc[6]
        R_706_728 = t706 * t.iloc[5] / t728 / t.iloc[6]
        R1.append(R_668_728.values[0])
        R2.append(R_706_728.values[0])
        print(R_668_728)
        print(R_706_728)

    df_R1[str(Te1)] = R1
    df_R2[str(Te1)] = R2
    
df_R1['ne'] = ne_range
df_R2['ne'] = ne_range

df_R1.to_excel('R_668_728.xlsx')
df_R2.to_excel('R_706_728.xlsx')

'''