# -*- coding: utf-8 -*-
"""
Created on Mon Nov  7 23:22:56 2022

@author: vaska
"""

import os
import pandas as pd
import numpy as np
import Stohastic_Model_Generator as m
import matplotlib
matplotlib.use('Agg') #save the figures to files instead of opening a window for each one
import matplotlib.pyplot as plt
import Plots as p

#folders of the repository (the paths work from any working directory)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'thesis_runs') #prices, scenarios and realizations used in the thesis
RESULTS = os.path.join(ROOT, 'results')
os.makedirs(RESULTS, exist_ok=True)

# In[]:
##initialize paramaters (price, scenarios etc.)

#determine the number of points
N=10
#time steps that we examine (t_0=0 mid price, t_0=4 very low price, t_0=19 very high price)
time_steps=[0, 4, 19]
#initial capacities of the battery (kWh)
initial_capacities=[1, 5, 7, 9, 13]
#tariff on the imported energy as a percentage of the MCP
tariffs=[0.3, 0]

#determine the number of scenarios
W=10 #for deterministic use W=1 for stohastic use any positive integer
flag=1 #1 for stohastic 0 for deterministic


def create_ln(lt_b, lt_s, N):
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
    return ln

# In[]:
##call the pyomo model and unpuck results for every time step, initial capacity and tariff

muf_results=[]
for t_0 in time_steps:
    # Read data, the prices and the scenarios start at the time step t_0 and end at the end of the day
    data = pd.read_excel(os.path.join(DATA, 'prices_'+str(t_0)+'.xlsx'))
    scenarios = pd.read_excel(os.path.join(DATA, 'scenarios_'+str(t_0)+'.xlsx'))
    data['p_load'] = scenarios.mean(axis=1) #only used when flag=0

    #lt_b and lt_s at t_0 (prices in euro/kWh)
    lt_b= data.MCP[0]*1.15
    lt_s= data.MCP[0]*0.85
    ln=create_ln(lt_b, lt_s, N)

    for initial_capacity in initial_capacities:
        for tariff in tariffs:
            e, loads, cost= m.model_generator_stohastic(data.time, data.MCP, data.p_load, ln, W, 0, initial_capacity, flag,
                                                        scenarios=scenarios, tariff=tariff, solver='appsi_highs')
            for i in range(N):
                muf_results.append([t_0, initial_capacity, tariff, ln[i], e[i], cost[i]])

            title='Συνάρτηση Οριακής Χρησιμότητας,t_0='+str(t_0)+', C_initial='+str(initial_capacity)+' kWh, Tariff='+('30%' if tariff else '0')
            file_name=os.path.join(RESULTS, 'MUF_t0_'+str(t_0)+'_C_'+str(initial_capacity)+'_tariff'+str(int(tariff*100))+'.png')
            p.plot_MUF(lt_b,lt_s, N, ln, e, title, file_name)
        print('MUFs for t_0='+str(t_0)+' and C_initial='+str(initial_capacity)+' kWh are ready')

muf_results=pd.DataFrame(muf_results, columns=['t_0', 'initial_capacity', 'tariff', 'ln', 'traded_energy', 'cost'])
muf_results.to_excel(os.path.join(RESULTS, 'MUF_results.xlsx'))
print('DataFrame is written to Excel File successfully.')

# In[]:
##realization: compare the stochastic model with the deterministic model that knows the load (t_0=0, C_initial=1 kWh, no tariff)

t_0=0
initial_capacity=1
data = pd.read_excel(os.path.join(DATA, 'prices_0.xlsx'))
scenarios = pd.read_excel(os.path.join(DATA, 'scenarios_0.xlsx'))
data['p_load'] = pd.read_excel(os.path.join(DATA, 'realization_0.xlsx')).iloc[:, 0]
lt_b= data.MCP[0]*1.15
lt_s= data.MCP[0]*0.85
ln=create_ln(lt_b, lt_s, N)

#deterministic: one scenario equal to the realization
e_real, loads, cost_real= m.model_generator_stohastic(data.time, data.MCP, data.p_load, ln, 1, 0, initial_capacity, 0, solver='appsi_highs')
#stohastic: the SARIMA scenarios
e_forecast, loads, cost_forecast= m.model_generator_stohastic(data.time, data.MCP, data.p_load, ln, W, 0, initial_capacity, 1,
                                                              scenarios=scenarios, solver='appsi_highs')

#percentage difference between the expected cost of the stohastic model and the optimal cost
error=[(cost_real[i]-cost_forecast[i])/cost_real[i]*100 for i in range(N)]

realization=pd.DataFrame({'ln':ln, 'cost_realization':cost_real, 'cost_forecast':cost_forecast, 'error_%':error,
                          'traded_energy_realization':e_real, 'traded_energy_forecast':e_forecast})
realization.to_excel(os.path.join(RESULTS, 'Realization-forecast costs.xlsx'))
print(realization)

# In[]:
#plot
##note that if an object is mutable (list, DFs etc.) any changes done to them in the functions
##will be done in the object that is located in our main code as well, should we want to avoid that a copy needs to be created


p.plot_MUF(lt_b,lt_s, N, ln, e_real, 'Realization', os.path.join(RESULTS, 'MUF_realization.png'))
p.plot_MUF(lt_b,lt_s, N, ln, e_forecast, 'Forecast', os.path.join(RESULTS, 'MUF_forecast.png'))
p.plot_scenarios(loads, data.p_load, W, os.path.join(RESULTS, 'scenarios_vs_realization.png'))

fig, ax = plt.subplots()
ax.plot(ln, error, '-o')
ax.set_xlabel('Τιμή της Ενέργειας στην P2P αγορά (€/kWh)')
ax.set_ylabel('Ποσοστιαίο Σφάλμα (%)')
ax.grid()
fig.savefig(os.path.join(RESULTS, 'realization_error.png'), bbox_inches='tight')
plt.close(fig)
