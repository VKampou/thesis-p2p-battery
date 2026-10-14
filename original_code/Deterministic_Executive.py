# -*- coding: utf-8 -*-
"""
Created on Mon Oct 17 20:16:17 2022

@author: vaska
"""


import pandas as pd
import matplotlib.pyplot as plt
import Determenistic_Model_Generator as m
import seaborn as sns

# In[1]:
##data collecting
    

# Read data
data = pd.read_excel("C:/Users/vaska/Storage/Python_Experiments/Thesis/input_data/data_deterministic.xlsx")

#build and solve the model

result = m.model_generator(data.time, data.MCP, data.p_load, solver='gurobi')

#set value for opeening capacity
closing_capacity = result.opening_capacity.shift(-1)


# assign name to the file and save it as xlsx
file_name = 'result_determenistic.xlsx'
result.to_excel(file_name)
print('DataFrame is written to Excel File successfully.')

# In[2]:
###data_processing 

result0 = result.drop(columns=['charge_power', 'discharge_power', 'p_load', 'opening_capacity','bought_power'],  axis=1)

result1=result.drop(columns=['MCP', 'p_load', 'opening_capacity','bought_power'],  axis=1)
result1=pd.melt(result1,['time'], value_name='power')

# In[3]:
##data plotting
##plot MCP

# set figure size
plt.figure( figsize = ( 12, 6))
  
sns.set_theme(style='whitegrid')

# using seaborn.lineplot()
sns.lineplot( x = 'time',
             y = 'MCP',
             data = result0)
        
  
plt.xlabel( 'Hour of the Day')

tickvalues = result.index

labellist = [ '00:00', '01:00', '02:00', '03:00', '04:00', '05:00', 
       '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', 
              '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00']

plt.xticks(ticks = tickvalues ,labels = labellist, rotation = 'vertical')

# In[3]:
##plot Charge and Discharge Power


# set figure size
plt.figure( figsize = ( 12, 6))
  
sns.set_theme(style="whitegrid")

# using seaborn.lineplot()
sns.barplot( x = 'time',
             y = 'power',
             hue='variable',
             data = result1)
            
  
plt.xlabel( 'Hour of the Day')
  
tickvalues = result.index

labellist = [ '00:00', '01:00', '02:00', '03:00', '04:00', '05:00', 
       '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', 
              '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00']

plt.xticks(ticks = tickvalues ,labels = labellist, rotation = 'vertical')