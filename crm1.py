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

def read_nist(nist_file,):
  data_nist = pd.read_excel(nist_file)
  for i in data_nist['Aki(s^-1)'].index:
    if data_nist['Aki(s^-1)'][i] == '  ':
      data_nist['Aki(s^-1)'][i] = '0'
  data_nist['Aki(s^-1)'] = data_nist['Aki(s^-1)'].astype(float)
  for j in ['conf_i', 'conf_k']:
    for i in data_nist[j].index:
      data_nist[j][i] = data_nist[j][i].replace(' ', '')
      if '1s.' in data_nist[j][i]:
        data_nist[j][i] = data_nist[j][i].replace('1s.', '')
        data_nist[j][i] = data_nist[j][i] + '1'
      if '2s.' in data_nist[j][i]:
        data_nist[j][i] = data_nist[j][i].replace('2s.', '')
        data_nist[j][i] = data_nist[j][i] + '1'
  data_nist = data_nist.replace({'1s2': '1s1'})
  return data_nist

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
  df_conf = df_conf.drop(['Energy'], axis=1)
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
  cols = ['Level_j', 'Level_i', 'A3', '5.00+02', '1.00+03', '2.00+03', '3.00+03', '5.00+03',
          '1.00+04', '1.50+04', '2.00+04', '3.00+04', '5.00+04', '1.00+05',
          '1.50+05', '2.00+05', '5.00+05']
  '''cols = ['Level_j', 'Level_i', 'A3', '1.16+04', '2.32+04', '5.80+04', '1.16+05',
        '2.32+05', '5.80+05', '1.16+06', '2.32+06', '5.80+06', '1.16+07',
        '2.32+07', '5.80+07', '1.16+08', '2.32+08']'''
  
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

def adas_Aij(Aki_adas, df_coef, lvl_i):
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

    df_coef['Aji'] = Aji['A3']
    df_coef['Aji'] = Aji['A3']
    
    return Aji, df_coef

def interp_coef(Te_val, temperature_range, df_to_interp):
  l = []
  for i in df_to_interp.index:    
    f1 = interp1d(temperature_range, df_to_interp[df_to_interp.columns[2:]].iloc[df_to_interp.index == i], kind='cubic')
    l.append(float(f1(Te_val)))
  return l

def coef_calc(df_ex, df_config, df_r, df_i, Te1, lvl_i):
  Te_range = [float(i) for i in df_ex.columns[2:]]
  df_ex[Te1] = interp_coef(Te1, Te_range, df_ex)
  Uex_Te = df_ex[{'Level_i', 'Level_j'	, Te1}].loc[(df_ex.Level_i == lvl_i) | (df_ex.Level_j == lvl_i)].reset_index(drop=True)
  for i in Uex_Te.iloc[Uex_Te.index<int(lvl_i)-1].index:
    Uex_Te.Level_j[i] = Uex_Te.Level_i[i]
    Uex_Te.Level_i[i] = lvl_i
  qji = const/df_config['degeneracy'].loc[df_config['Level_i'] != lvl_i].reset_index(drop=True) * (
  IH/kB/float(Te1)*eV)**0.5 * Uex_Te[Te1].reset_index(drop=True)
  dE = df_config['Energy_eV'].loc[df_config['Level_i'] != lvl_i] - float(df_config['Energy_eV'].loc[df_config['Level_i'] == lvl_i])
  exp_calc = np.exp(dE/kB/float(Te1)*eV)
  factor = df_config['degeneracy'].loc[df_config['Level_i'] != lvl_i] / float(df_config['degeneracy'].loc[df_config['Level_i'] == lvl_i]) * exp_calc
  qij = factor.reset_index(drop=True) * qji
  
  df_r[Te1] = interp_coef(Te1, Te_range, df_r)
  df_i[Te1] = interp_coef(Te1, Te_range, df_i)

  rec_coef_df, ion_coef_df = df_r[{'Level_i'	, Te1}], df_i[{'Level_i'	, Te1}]
  #Si = float(ion_coef_df[Te1].loc[ion_coef_df.Level_i==lvl_i])
  Si = float(ion_coef_df[Te1].loc[ion_coef_df.Level_i==lvl_i])  / np.exp(float(df_config['Energy_eV'].loc[df_config['Level_i'] == lvl_i])/kB/float(Te1)*eV) # / ioniz by exp?
  R = float(rec_coef_df[Te1].loc[rec_coef_df.Level_i==lvl_i])
  
  df_coef = pd.DataFrame(data = Uex_Te[{'Level_j', 'Level_i'}])
  df_coef['qij'] = qij
  df_coef['qji'] = qji
  df_coef['Si'] = Si
  df_coef['R'] = R

  return qij, qji, Si, R, df_coef

# NIST data pre processing 
def nist_preproc(df_nist, df_config, df_coef, lvl_i):
  df_nist = df_nist.replace({'1s2': '1s1'})
  l = []
  for i in df_nist.index:
    for j in df_config['Configuration'].index:
      if df_nist['conf_i'][i] == df_config['Configuration'][j] and df_nist['J_i'][i] == df_config['J'][j]:
        for k in df_config['Configuration'].index:
          if df_nist['conf_k'][i] == df_config['Configuration'][k] and df_nist['J_k'][i] == df_config['J'][k]:
            l.append(i)

  df_A = df_nist.iloc[l]

  l1 = []
  l2 = []
  idx_to_del = []
  for j in ['1', '2']:
    if j == '1':
      col_str = 'conf_i'
      j_str = 'J_i'
    else: 
      col_str = 'conf_k'
      j_str = 'J_k'
    l = []
    temp = [['1s1', 0], ['2s1', 1], ['2s1', 0], ['2p1', 4], ['2p1', 1], ['3s1', 1], ['3s1', 0], ['3p1', 4],
            ['3d1', 7], ['3d1', 2], ['3p1', 1], ['4s1', 1], ['4s1', 0], ['4p1', 4], ['4d1', 7], ['4d1', 2],
            ['4f1', 1], ['4f1', 3], ['4p1', 1]] 

    for i in df_A.index:
      if df_A[col_str][i] == '1s1' :
          l.append('1')
      elif df_A[col_str][i]== '2s1' and df_A[j_str][i]== 1:
          l.append('2')     
      elif df_A[col_str][i]== '2s1' and df_A[j_str][i]== 0:
          l.append('3')  
      elif df_A[col_str][i]== '2p1' and df_A[j_str][i]== 4:
          l.append('4')  
      elif df_A[col_str][i]== '2p1' and df_A[j_str][i]== 1:
          l.append('5')  
      elif df_A[col_str][i]== '3s1' and df_A[j_str][i]== 1:
          l.append('6')  
      elif df_A[col_str][i]== '3s1' and df_A[j_str][i]== 0:
          l.append('7')     
      elif df_A[col_str][i]== '3p1' and df_A[j_str][i]== 4:
          l.append('8')  
      elif df_A[col_str][i]== '3d1' and df_A[j_str][i]== 7:
          l.append('9')  
      elif df_A[col_str][i]== '3d1' and df_A[j_str][i]== 2:
          l.append('10')  
      elif df_A[col_str][i]== '3p1' and df_A[j_str][i]== 1:
          l.append('11')  
      elif df_A[col_str][i]== '4s1' and df_A[j_str][i]== 1:
          l.append('12')     
      elif df_A[col_str][i]== '4s1' and df_A[j_str][i]== 0:
          l.append('13')  
      elif df_A[col_str][i]== '4p1' and df_A[j_str][i]== 4:
          l.append('14')  
      elif df_A[col_str][i]== '4d1' and df_A[j_str][i]== 7:
          l.append('15')  
      elif df_A[col_str][i]== '4d1' and df_A[j_str][i]== 2:
          l.append('16')  
      elif df_A[col_str][i]== '4f1' and df_A[j_str][i]== 1:
          l.append('17')     
      elif df_A[col_str][i]== '4f1' and df_A[j_str][i]== 3:
          l.append('18')  
      elif df_A[col_str][i]== '4p1' and df_A[j_str][i]== 1:
          l.append('19')  
      else: idx_to_del.append(i)
    if j == '1':
      l1 = l
    else: 
      l2 = l

  df_A['Level_i'] = l1
  df_A['Level_j'] = l2

  df_A = df_A.loc[df_A.Acc == 'AAA']
  print(df_A)
  Aji = df_A[{'Level_i', 'Level_j'	, 'Aki(s^-1)'}].loc[df_A.Level_i == lvl_i].reset_index(drop=True)
  Aji = Aji.rename(columns = {'Aki(s^-1)' : 'Aki'})
  l = []
  for i in list(range(1, 20)):
    if str(i) not in list(Aji.Level_j) and i != int(lvl_i):
      l.append(str(i))

  s = pd.DataFrame()
  s['Aki'] = [1e-30]* len(l)
  s['Level_j'] = l
  s['Level_i'] = lvl_i
  Aji = pd.concat([Aji, s], axis = 0)
  Aji.Level_j=Aji.Level_j.astype(int)
  Aji = Aji.sort_values('Level_j').reset_index(drop=True)
  Aji.Level_j=Aji.Level_j.astype(str)
  df_coef['Aji'] = Aji['Aki']
  df_coef['Aji'] = Aji['Aki']

  return Aji, df_coef

def matrix_cols_calc(ne, Si, qij, df_coef, lvl_i):
  mask_idx_Aji =  df_coef.iloc[df_coef.index < int(lvl_i)-1].index
  m_Aji = df_coef
  m_Aji.Aji[mask_idx_Aji] = 1e-30
  mask_idx_Aij =  df_coef.iloc[df_coef.index > int(lvl_i)-1].index
  m_Aij = df_coef
  m_Aij.Aji[mask_idx_Aij] = 1e-30
  Cii = -sum(ne*df_coef['Si']/18 + ne*df_coef['qij'] + m_Aij.Aji)
  Cij =  m_Aji.Aji + ne*df_coef['qji'] #? check if it works correctly
  C_temp = list(Cij)
  C_temp.insert(int(lvl_i)-1, Cii)
  lvl_vector = pd.DataFrame(data = C_temp, columns = [str('lvl_') + lvl_i])
  
  return lvl_vector

#constants
ion_potential = 198310.8
eV = 8.61732814974056E-05
h = 4.135667669e-15 #eV*s
c = 29979245800 #cm/s
const = 2.1716e-8 #cm3 s-1 #for excitation rate coef
IH = 13.6048 #eV
kB = 8.617e-5 #eV/K

# df_nist = read_nist('/content/drive/MyDrive/CRM_data/data_nist.xlsx')
df_nist = read_nist('data_nist.xlsx')
#df_ex, df_i, df_config = read_adas4("/content/drive/MyDrive/CRM_data/helike_hps02he.dat", 'S') 
# df_ex, df_i, df_config = read_adas4("/content/drive/MyDrive/CRM_data/helike_pb04he0.dat", 'S') 
df_ex, df_i, df_config, Aki_adas = read_adas4("helike_pb04he0.dat", 'S') 
_, df_r, _, _ = read_adas4("helike_kvi97#he0.dat", 'R')

Te1 = input('Choose temperature in range [0.043087, 43.086641] eV \n')
ne = float(input('Choose electron density in X*e+13 cm**-3 \n')) * 1e13  # Electron density in cm**-3

"""
Стационарный случай - 
# 0 = C * n *2..19* + C'
"""
Aji_full = pd.DataFrame()
df_M =  pd.DataFrame()
for i in list(range(1, 20)):
  qij, qji, Si, R, df_coef = coef_calc(df_ex, df_config, df_r, df_i, Te1, str(i))
  #Aji, df_coef = nist_preproc(df_nist, df_config, df_coef, str(i))
  Aji, df_coef = adas_Aij(Aki_adas, df_coef, str(i))
  #print(Aji)
  Aji_full = pd.concat([Aji_full, Aji])
  df_M[str('lvl_') + str(i)] = matrix_cols_calc(ne, Si, qij, df_coef, str(i))

df_M = df_M.drop(0, axis = 0)
C1 = df_M.lvl_1 * (-1)
C = df_M.drop('lvl_1', axis = 1)

x = np.linalg.solve(C, C1) # only sq matrix

print(x)

# check Aji

t = pd.DataFrame(x)

t668 = float(Aji_full.A3.loc[(Aji_full.Level_i == '5')&(Aji_full.Level_j == '10')])
t728 = float(Aji_full.A3.loc[(Aji_full.Level_i == '5')&(Aji_full.Level_j == '7')])
t706 = float(Aji_full.A3.loc[(Aji_full.Level_i == '4')&(Aji_full.Level_j == '6')])

R_668_728 = t668 * t.iloc[9] / t728 / t.iloc[6]
R_706_728 = t706 * t.iloc[5] / t728 / t.iloc[6]

print(t668 * t.iloc[9] / t728 / t.iloc[6])
print(t706 * t.iloc[5] / t728 / t.iloc[6])

R1 = []
R2 = []

for m in np.linspace(1e12, 1e13,10):
    ne = m
    for k in np.linspace(5, 40, 10):
        Te1 = k
        Aji_full = pd.DataFrame()
        df_M =  pd.DataFrame()
        for i in list(range(1, 20)):
          qij, qji, Si, R, df_coef = coef_calc(df_ex, df_config, df_r, df_i, Te1, str(i))
          Aji, df_coef = adas_Aij(Aki_adas, df_coef, str(i))
          Aji_full = pd.concat([Aji_full, Aji])
          df_M[str('lvl_') + str(i)] = matrix_cols_calc(ne, Si, qij, df_coef, str(i))
    
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
        R1.append(R_668_728.values)
        R2.append(R_706_728.values)
        print(R_668_728)
        print(R_706_728)








