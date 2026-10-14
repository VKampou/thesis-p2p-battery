# -*- coding: utf-8 -*-
"""
Created on Sat Nov  5 17:13:50 2022

@author: vaska
"""

import pandas as pd
import pyomo.environ as pyo
import pyomo.opt as op
import numpy as np
import logging

def model_generator_stohastic(time, MCP, p_load, ln, number_of_scenarios, t_0, initial_capacity, solve_stohastic, scenarios=None, tariff=0, include_revenue=True, solver: str='appsi_highs'):
    
# In[]:
##initialize and create model and model components

    ##battery specs
    MIN_model_CAPACITY = 0
    MAX_model_CAPACITY = 13
    MAX_model_POWER = 7
    INITIAL_CAPACITY = initial_capacity
    EFFICIENCY = 0.9
    flag=solve_stohastic
    
    
    ##initialize data
    df = pd.DataFrame({'time': time, 'MCP': MCP, 'p_load': p_load}).reset_index(drop=True)
    df['index'] = df.index
    ln=ln
    W=number_of_scenarios
    t_0=t_0
    T= len(df.index)
    
    
    # Define model and solver
    model = pyo.ConcreteModel()
    opt = op.SolverFactory(solver)
 
    ##sets
    model.Period = pyo.Set(initialize=list(df.index), ordered=True)
    model.Scenario=pyo.Set(initialize=range(W)) #uncertainty set
    
    #parameters
    model.Price = pyo.Param(initialize=list(df.MCP), within=pyo.Any) #non-indexed (Scalar) parameter
    model.Load=pyo.Param(model.Period, model.Scenario, mutable=True)

    ##variables
    model.Charge_power = pyo.Var(model.Period, model.Scenario, bounds=(0, MAX_model_POWER))
    model.Discharge_power = pyo.Var(model.Period, model.Scenario, bounds=(0, MAX_model_POWER))
    model.Capacity = pyo.Var(model.Period, model.Scenario, bounds=(MIN_model_CAPACITY, MAX_model_CAPACITY))
    model.Bought_power= pyo.Var(model.Period, model.Scenario, bounds=(0, 1000000000))
    model.Sold_power = pyo.Var(model.Period, model.Scenario, bounds=(0, 1000000))
    model.Binary_u=pyo.Var(model.Period, model.Scenario, domain=pyo.Binary)
    model.Binary_b=pyo.Var(model.Period, model.Scenario, domain=pyo.Binary)
    model.Binary_g=pyo.Var(model.Period, model.Scenario, domain=pyo.Binary)
    model.Traded_energy_future=pyo.Var(model.Period, model.Scenario, bounds=(-1000000, 500000)) 
    model.Traded_energy=pyo.Var(within=pyo.Reals, bounds=(-10000000, 5000000)) # first stage decision variable
    model.Imported_energy=pyo.Var(model.Period, model.Scenario, within=pyo.NonNegativeReals) #oi metablhtes aytes ekfrazoyn thn fysikh roh energeias panw stis grammes opote prepei na theorisoyme kati to reallistiko de mporei se grammh
    model.Exported_energy=pyo.Var(model.Period, model.Scenario, within=pyo.NonNegativeReals) #dianomhs na exoyme 1000kw isxy as poume, ta 15kw einai pio realistiko
# In[]:
##decide model to solve    
##generate the scanarios for the load
##save the values at the model.Load variable
##we obviously cannot simulate all the posible outcomes, the best we can do is find a representive group of scenarios and assign the proper weight with respect to each scenarios probabillity


    if flag==1:#solve stohastic
        loads=pd.DataFrame()
        a=[]
        weight=[]
        for w in range(W):
            for t in range(T):
                if scenarios is not None: #use the scenarios made by the SARIMA model (Scenarios.py)
                    s=float(scenarios.iloc[t, w])
                else:
                    sigma = 0.1
                    s=np.random.normal(df.loc[t].at['p_load'], sigma, 1)
                    s=float(s[0]) #we need to define s as a float because model.Load[t, w]=s won't work if s is an array or a list
                model.Load[t, w] = s 
                a.append(s) #save the load values temporary so we can store them in the df
            loads['scenario '+str(w)]=a
            a.clear() #clear the temporary memory to reuse it in the next interation
        for i in range(W):
            weight.append(1/W)
    else: #solve deterministic so W=1
        loads=pd.DataFrame()
        a=[]
        weight=[]
        for w in range(W):
            for t in range(T):
                s=df.loc[t].at['p_load']
                s=float(s)
                model.Load[t, w] = s
                a.append(s)
            loads['scenario '+str(w)]=a
            a.clear()
        for i in range(W):
            weight.append(1/W)
        
# In[]:
##create the constraints

    def only_charge(model, t, w):
        return  model.Charge_power[t, w] <= model.Binary_u[t, w]*MAX_model_POWER / EFFICIENCY 
    model.only_charge=pyo.Constraint(model.Period, model.Scenario, rule=only_charge)
            
    
    def only_discharge(model, t, w):
        return  model.Discharge_power[t, w] <= (1-model.Binary_u[t, w])*MAX_model_POWER * EFFICIENCY
    model.only_discharge=pyo.Constraint(model.Period, model.Scenario,rule=only_discharge) 
      
    
    def only_buy(model, t, w):
        return model.Bought_power[t, w] <= model.Imported_energy[t, w]
    model.only_buy=pyo.Constraint(model.Period, model.Scenario, rule=only_buy)
       
    def only_sell(model, t, w):
        return model.Sold_power[t, w] <= model.Exported_energy[t, w]   
    model.only_sell=pyo.Constraint(model.Period, model.Scenario, rule=only_sell)
    
    
    def only_import(model, t, w):
        return model.Imported_energy[t, w] <= (model.Binary_g[t, w])*1000 #a bigger M (e.g. 1e27) breaks the solver numerically
    model.only_import=pyo.Constraint(model.Period, model.Scenario, rule=only_import)
       
    def only_export(model, t, w):
        return model.Exported_energy[t, w] <= (1-model.Binary_g[t, w])*1000
    model.only_export=pyo.Constraint(model.Period, model.Scenario, rule=only_export)
    
    def over_charge(model, t, w):
            return  model.Charge_power[t, w] <= ((MAX_model_CAPACITY - model.Capacity[t, w] / 1) / EFFICIENCY) 
    model.over_charge = pyo.Constraint(model.Period, model.Scenario, rule=over_charge)
       
    # Make sure the model discharge the amount it actually has
    def over_discharge(model, t, w):
            return  model.Discharge_power[t, w] <= model.Capacity[t, w] * EFFICIENCY
    model.over_discharge = pyo.Constraint(model.Period, model.Scenario, rule=over_discharge)
    
    # Defining capacity rule for the model
    def capacity_constraint(model, t, w):
            # Assigning model's starting capacity at the beginning
            if t == model.Period.first():
                return model.Capacity[t, w] == INITIAL_CAPACITY
            # if not update the capacity normally    
            return model.Capacity[t, w] == (model.Capacity[t-1, w]
                                            + (model.Charge_power[t-1, w] * 1 * EFFICIENCY)  #bazw *1 giati exoyme mia wra ean eixame mish tha ebaza *(1/2)
                                            - (model.Discharge_power[t-1, w] * 1 / EFFICIENCY))
    model.capacity_constraint = pyo.Constraint(model.Period, model.Scenario, rule=capacity_constraint)
        
       
    def final_capacity(model, w):
           return model.Capacity[model.Period.last(), w]==initial_capacity + model.Discharge_power[model.Period.last(), w] 
    model.final_capacity_constraint=pyo.Constraint(model.Scenario, rule=final_capacity)
    
    def energy_equilibrium_t0(model, w):
           return model.Traded_energy==model.Charge_power[t_0, w] + model.Load[t_0, w] - model.Discharge_power[t_0, w]-model.Bought_power[t_0, w]+model.Sold_power[t_0, w]
    model.energy_equilibrium_t0=pyo.Constraint(model.Scenario, rule=energy_equilibrium_t0) 
    
    def energy_equilibrium_t(model, t, w):
           return model.Traded_energy_future[t, w]==model.Charge_power[t, w] + model.Load[t, w] - model.Discharge_power[t, w] -model.Bought_power[t, w]+model.Sold_power[t, w]
    model.energy_equilibrium_t=pyo.Constraint(model.Period, model.Scenario, rule=energy_equilibrium_t)
    
    
    def energy_equilibrium_x(model, t, w):
           return model.Imported_energy[t, w]==model.Charge_power[t, w] + model.Load[t, w] - model.Discharge_power[t, w] + model.Exported_energy[t, w]
    model.energy_equilibrium_x=pyo.Constraint(model.Period, model.Scenario, rule=energy_equilibrium_x)
    
    # Make sure the model do not discharge when price are not positive
    def negative_discharge(model, t, w):
            # if the spot price is not  positive, suppress discharge
            if  model.Price.extract_values_sparse()[None][t]<= 0:
                return model.Discharge_power[t, w] == 0
            # otherwise skip the current constraint    
            return pyo.Constraint.Skip
    model.negative_discharge = pyo.Constraint(model.Period, model.Scenario, rule=negative_discharge)   
    
    # In[]:
    ##create the objective function for each ln value 
    
    traded_energy=[]
    obj_value=[]

    for i in range(len(ln)):
        def minimize_cost(model):
            f1 = ln[i]*model.Traded_energy
            #print(ln)
            f2=[]
            f3=[]
            for w in model.Scenario:
                for t in model.Period:
                    #prices in euro/kWh: lt_b=1.15*MCP, lt_s=0.85*MCP and the tariff is charged only on imported energy
                    f2.append(weight[w]*((model.Price.extract_values_sparse()[None][t]*1.15)*model.Bought_power[t, w]-(model.Price.extract_values_sparse()[None][t]*0.85)*model.Sold_power[t, w]
                                         +tariff*model.Price.extract_values_sparse()[None][t]*model.Imported_energy[t, w]) )
            for w in model.Scenario:    
                for t in range(model.Period.first()+1, model.Period.last()+1 ): 
                    f3.append(weight[w]*(model.Traded_energy_future[t, w]*model.Price.extract_values_sparse()[None][t]))
            sum_1=sum(f2)
            sum_2=sum(f3)
            #print(sum_1)
            return sum_1+sum_2+f1
             
        
        if i>0:
            model.del_component(model.objective) #remove the objective of the previous ln value
        model.objective = pyo.Objective(rule=minimize_cost, sense=pyo.minimize)
# In[]:
##solve the problem and unpuck the results
             
        # Maximise the objective
        opt.solve(model, tee=False)
        traded_energy.append(model.Traded_energy.value) 
        obj_value.append(model.objective())
        
# In[]:
#ignore warnings and return values
        
        logging.getLogger('pyomo.core').setLevel(logging.ERROR)
    
    return traded_energy, loads, obj_value

# In[]:
##that code can be used if you want to get insight on the model variables
        
'''
#Store the results in a DataFrame 
charge_power =[]
discharge_power= [] 
capacity= [] 
bought_power=[]
sold_power=[]
load=[]
traded_energy=[]
for t in range(model.Period.first(), model.Period.last() + 1): #we include +1 because range in python is non inclusive so if we want batter.Period_last() as wellwe meed to add +1 to get it
    charge_power.append(model.Charge_power[t, 0].value)
    discharge_power.append(model.Discharge_power[t, 0].value)
    capacity.append(model.Capacity[t, 0].value)
    bought_power.append(model.Bought_power[t, 0].value)
    sold_power.append(model.Sold_power[t, 0].value)
    load.append(model.Load[t, 0].value)
    if t==model.Period.first():
        traded_energy.append(model.Traded_energy.value)
    else: 
        traded_energy.append(model.Traded_energy_future[t, 0].value)

result_1 = pd.DataFrame({ 'load':load, 'bought_power':bought_power, 'sold_power':sold_power, 'traded_energy':traded_energy,  'charge_power':charge_power, 'discharge_power':discharge_power, 'opening_capacity':capacity})   
result_2=model.Traded_energy.value

obj_value=model.objective()

return result_1, result_2, obj_value

'''