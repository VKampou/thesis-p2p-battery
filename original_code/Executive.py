# -*- coding: utf-8 -*-
"""
Created on Mon Nov  7 23:22:56 2022

@author: vaska
"""

import pandas as pd
import numpy as np
import model_generator_stohastic as m
import matplotlib.pyplot as plt
import plots as p

# In[]:
##initialize paramaters (price, scenarios etc.) 

# Read data
data = pd.read_excel('C:/Users/vaska/Desktop/ΔΙΠΛΩΜΑΤΙΚΗ/DEMO_DATA_LP_STOHASTIC.xlsx')

#determine the number of points
N=15
#initial time_step
t_0=0 
#determine the median price for ln in t00
lt_b= 130
lt_s= 74

#create a range of the ln values 
ln=[]
for i in range(N):
   if i==0 :
       a=lt_s*1.01
   elif i==N-1:
    a=lt_b*0.99
   else:
    a=lt_s+i*(lt_b-lt_s)/N
   ln.append(a)
   
#determine the number of scenarios
W=20 #for deterministic use W=1 for stohastic use any positive integer
flag=1 #1 for stohastic 0 for deterministic

initial_capacity=10

# In[]:
##call the pyomo model and unpuck results

e, loads,cost= m.model_generator_stohastic(data.time, data.MCP, data.p_load, ln, W, t_0, initial_capacity, flag, solver='gurobi')

file_name = 'loads.xlsx'
loads.to_excel(file_name)
print('DataFrame is written to Excel File successfully.')
print(cost)

# In[]:
#plot
##note that if an object is mutable (list, DFs etc.) any changes done to them in the functions
##will be done in the object that is located in our main code as well, should we want to avoid that a copy needs to be created


p.plot_MUF(lt_b,lt_s, N, ln, e)
p.plot_scenarios(loads, data.p_load, W)