# -*- coding: utf-8 -*-
"""
Created on Mon Oct 17 19:09:35 2022

@author: vaska
"""

import pandas as pd
import pyomo.environ as pyo
import pyomo.opt as op
import numpy as np


def model_generator(time, MCP, p_load, initial_capacity=10, include_revenue=True, solver: str='gurobi'):
   
    
    
    # model's technical specification
        
    MIN_model_CAPACITY = 0
    MAX_model_CAPACITY = 13
    MAX_model_POWER = 7
    INITIAL_CAPACITY = initial_capacity
    EFFICIENCY = 0.9
    
    
    df = pd.DataFrame({'time': time, 'MCP': MCP, 'p_load': p_load}).reset_index(drop=True)
    df['index'] = df.index
   

    # Define model and solver
    model = pyo.ConcreteModel()
    opt = op.SolverFactory(solver)
    
    # defining components of the objective model
    # model parameters
    model.Period = pyo.Set(initialize=list(df.index), ordered=True) #Sets provide indexes for parameters, variables and other sets. 
    model.Price = pyo.Param(initialize=list(df.MCP), within=pyo.Any)
    model.Load=pyo.Param(initialize=list(df.p_load), within=pyo.Any)
    

    # model varaibles
    model.Capacity = pyo.Var(model.Period, bounds=(MIN_model_CAPACITY, MAX_model_CAPACITY))
    model.Charge_power = pyo.Var(model.Period, bounds=(0, MAX_model_POWER))
    model.Discharge_power = pyo.Var(model.Period, bounds=(0, MAX_model_POWER))
    model.Bought_power=pyo.Var(model.Period)
    model.Binary=pyo.Var(model.Period, domain=pyo.Binary)
    
    
    #Defining the model objective (function to be maximise)
    def minimize_cost(model):
            rev = sum(df.MCP[t] * ((model.Discharge_power[t] / 1) )  for t in model.Period) #ama eksetazame ana 30lepta tha eprepe na baloume /2 giati exoyme thn mish wra fortishs oxi oloklhrh
            cost_1 = sum(df.MCP[t] * (model.Charge_power[t] / 1)  for t in model.Period)
            cost_2 = sum(df.MCP[t] * model.Bought_power[t] for t in model.Period)
            #print(cost_1)
            #print(cost_2)
            return cost_1+cost_2-rev
        
    model.objective = pyo.Objective(rule=minimize_cost, sense=pyo.minimize)

    #Create model's constraints

    # Make sure the model does not charge above the limit
    def over_charge(model, t):
            return model.Charge_power[t] <= ((MAX_model_CAPACITY - model.Capacity[t] / 1) / EFFICIENCY) #gia na sygkrinw paromoia pragmata prepei na kanw thn energeia isxy opote kanw /  gia na diairesw me mia wra, ean hthlea mish tha ekana /(1/2)) thimizw oti energeia=isxys*xronos antistoixa isxys =energeia/xronos

    # Make sure the model discharge the amount it actually has
    def over_discharge(model, t):
            return model.Discharge_power[t] <= model.Capacity[t] * EFFICIENCY

    # Make sure the model do not discharge when price are not positive
    def negative_discharge(model, t):
            # if the spot price is not  positive, suppress discharge
            if model.Price.extract_values_sparse()[None][t] <= 0:
                return model.Discharge_power[t] == 0
            # otherwise skip the current constraint    
            return pyo.Constraint.Skip

    # Defining capacity rule for the model
    def capacity_constraint(model, t):
            # Assigning model's starting capacity at the beginning
            if t == model.Period.first():
                return model.Capacity[t] == INITIAL_CAPACITY
            # if not update the capacity normally    
            return model.Capacity[t] == (model.Capacity[t-1] 
                                            + (model.Charge_power[t-1] * 1 * EFFICIENCY)  #bazw *1 giati exoyme mia wra ean eixame mish tha ebaza *(1/2)
                                            - (model.Discharge_power[t-1] * 1 / EFFICIENCY) )
        
    #energy equilibrium at the grids side    
    def energy_equilibrium(model, t):
            return model.Bought_power[t]==model.Charge_power[t] + df.p_load[t] - model.Discharge_power[t] 
        
    def only_charge(model, t):
          return  model.Charge_power[t] <= model.Binary[t]*MAX_model_POWER / EFFICIENCY
          
       
    def only_discharge(model, t):
           return model.Discharge_power[t] <= (1-model.Binary[t])*MAX_model_POWER * EFFICIENCY
     
    #final capacity must be equal to the initial 
    def final_capacity_constaint(model, t): 
          return model.Capacity[model.Period.last()]==initial_capacity + model.Discharge_power[model.Period.last()] 
    
   
    #Set constraints for the model
    model.capacity_constraint = pyo.Constraint(model.Period, rule=capacity_constraint)
    model.over_charge = pyo.Constraint(model.Period, rule=over_charge)
    model.over_discharge = pyo.Constraint(model.Period, rule=over_discharge)
    model.negative_discharge = pyo.Constraint(model.Period, rule=negative_discharge)
    model.energy_equilibrium=pyo.Constraint(model.Period, rule=energy_equilibrium)
    model.only_charge=pyo.Constraint(model.Period, rule=only_charge)
    model.only_discharge=pyo.Constraint(model.Period,rule=only_discharge)
    model.final_capacity_constraint=pyo.Constraint(model.Period,rule=final_capacity_constaint)
        
    # Maximise the objective
    opt.solve(model, tee=False)
    
    
    #Store the results in a DataFrame 
    charge_power =[]
    discharge_power= [] 
    capacity= [] 
    bought_power= [] 
    MCP = [] 
    for t in range(model.Period.first(), model.Period.last() + 1): #we include +1 because range in python is non inclusive so if we want batter.Period_last() as wellwe meed to add +1 to get it
        charge_power.append(model.Charge_power[t].value)
        discharge_power.append(model.Discharge_power[t].value)
        capacity.append(model.Capacity[t].value)
        bought_power.append(model.Bought_power[t].value)
        MCP.append(df.MCP[t])
    
    
    result = pd.DataFrame({'time':time, 'MCP':MCP, 'p_load': p_load, 'bought_power': bought_power,  'charge_power':charge_power,
                           'discharge_power':discharge_power, 'opening_capacity':capacity})
    
  
    return result
