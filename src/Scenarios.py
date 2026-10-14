# -*- coding: utf-8 -*-
"""
Created on Thu Dec 22 22:38:52 2022

@author: vaska
"""

# Import libraries
import os
import warnings
import itertools
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') #save the figures to files instead of opening a window for each one
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn.metrics import mean_squared_error

#folders of the repository (the paths work from any working directory)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, 'results')
os.makedirs(RESULTS, exist_ok=True)

#the AIC grid search fits 128 models and takes a long time, the best model is used directly below
RUN_GRID_SEARCH = False

# In[]:   
# Defaults for plots 
plt.rcParams['figure.figsize'] = (20.0, 10.0)
plt.rcParams.update({'font.size': 12})
plt.style.use('ggplot')

# In[]:  
# Load the data
data = pd.read_excel(os.path.join(ROOT, 'data', 'raw', 'data_set.xlsx'), skipfooter=3)
# A bit of pre-processing to make it nicer
data['timestamp']=pd.to_datetime(data['timestamp'], format='%Y-%m-%d %H')
data.set_index(['timestamp'], inplace=True)
data = data.asfreq('h')

# Plot the data (first 15 days, Fig. 16)
data[:'2018-01-15 23:00:00'].plot()
plt.ylabel('Energy Consumption')
plt.xlabel('Date')
plt.savefig(os.path.join(RESULTS, 'load_history.png'), bbox_inches='tight')
plt.close()

# In[]:  
#find best paramaters for the model

# Define the d and q parameters to take any value between 0 and 1
q = d = range(0, 2)
# Define the p parameters to take any value between 0 and 3
p = range(0, 4)

# Generate all different combinations of p, q and q triplets
pdq = list(itertools.product(p, d, q))

# Generate all different combinations of seasonal p, q and q triplets
seasonal_pdq = [(x[0], x[1], x[2], 24) for x in list(itertools.product(p, d, q))]

print('Examples of parameter combinations for Seasonal ARIMA...')
print('SARIMAX: {} x {}'.format(pdq[1], seasonal_pdq[1]))
print('SARIMAX: {} x {}'.format(pdq[1], seasonal_pdq[2]))
print('SARIMAX: {} x {}'.format(pdq[2], seasonal_pdq[3]))
print('SARIMAX: {} x {}'.format(pdq[2], seasonal_pdq[4]))

#the model is trained up to 2018-03-02 and forecasts the next day, 2018-03-03 (the realization of the thesis)
train_data = data['2018-01-01 02:00:00':'2018-03-02 23:00:00']
test_data = data['2018-03-03 00:00:00':'2018-03-03 23:00:00']

warnings.filterwarnings("ignore") # specify to ignore warning messages


if RUN_GRID_SEARCH:
    AIC = []
    SARIMAX_model = []
    for param in pdq:
        for param_seasonal in seasonal_pdq:
            try:
                mod = sm.tsa.statespace.SARIMAX(train_data,
                                                order=param,
                                                seasonal_order=param_seasonal,
                                                enforce_stationarity=False,
                                                enforce_invertibility=False)

                results = mod.fit()

                print('SARIMAX{}x{} - AIC:{}'.format(param, param_seasonal, results.aic), end='\r')
                AIC.append(results.aic)
                SARIMAX_model.append([param, param_seasonal])
            except:
                continue
        
    print('The smallest AIC is {} for model SARIMAX{}x{}'.format(min(AIC), SARIMAX_model[AIC.index(min(AIC))][0],SARIMAX_model[AIC.index(min(AIC))][1]))
#the combination with the snmallest AIC is (3,0,1)x(1,,0,1, 24)

# In[]:
#fit the model for the optimal paramaters   
start_train='2018-01-01 02:00:00'
end_train='2018-03-02 23:00:00'
start_test='2018-03-03 00:00:00'
end_test= '2018-03-03 23:00:00'

# Let's fit this model
train_data = data[start_train:end_train]
test_data = data[start_test:end_test]
mod = sm.tsa.statespace.SARIMAX(train_data,
                                order=(3, 0, 1),
                                seasonal_order=(2,1,1,24),
                                enforce_stationarity=False,
                                enforce_invertibility=False)

results = mod.fit()


# In[]:
#few insights

results.plot_diagnostics(figsize=(20, 14))
plt.savefig(os.path.join(RESULTS, 'diagnostics.png'), bbox_inches='tight')
plt.close()

# In[]:
#now let's visualize


pred0 = results.get_prediction(start='2018-03-01 00:00:00', end=end_test, dynamic=False)
pred0_ci = pred0.conf_int()

pred1 = results.get_prediction(start='2018-03-01 00:00:00',end=end_test,   dynamic=True)
pred1_ci = pred1.conf_int()

pred2 = results.get_forecast(end_test)
pred2_ci = pred2.conf_int()
print(pred2.predicted_mean[start_test:end_test])

ax = data[:end_test].plot(figsize=(20, 16))
pred0.predicted_mean.plot(ax=ax, label='1-step-ahead Forecast (get_predictions, dynamic=False)')
pred1.predicted_mean.plot(ax=ax, label='Dynamic Forecast (get_predictions, dynamic=True)')
pred2.predicted_mean.plot(ax=ax, label='Dynamic Forecast (get_forecast)')
ax.fill_between(pred2_ci.index, pred2_ci.iloc[:, 0], pred2_ci.iloc[:, 1], color='k', alpha=.1)
plt.ylabel('Energy Consumption')
plt.xlabel('Date')
plt.legend()
plt.xlim('2018-03-01 00:00:00', end_test)
plt.savefig(os.path.join(RESULTS, 'forecast.png'), bbox_inches='tight')
plt.close()


# In[]:
#evaluate result

prediction = pred2.predicted_mean[start_test:end_test].values
# flatten nested list
truth = list(itertools.chain.from_iterable(test_data.values))
# Mean Absolute Percentage Error
MAPE = np.mean(np.abs((truth - prediction) / truth)) * 100

print('The Mean Absolute Percentage Error for the forecast of the next day is {:.2f}%'.format(MAPE))

######

# Calculate the mean squared error
mse = mean_squared_error(prediction, truth)

# Calculate the root mean squared error
rmse = np.sqrt(mse)

#Calculate the root mean squared error per cent
rmse_per_cent=rmse*100


print('The Root Mean Square Error for the forecast of the next day is {:.2f}%'.format(rmse_per_cent))



# In[]:
#create scenarios


# Get the forecast values as a numpy array
forecast_values = pred2.predicted_mean.values
forecast_values = forecast_values[-24:] #we only care for the last 24 elements

# Get the time values of the forecast as a numpy array
forecast_times = pred2.predicted_mean.index.to_numpy()
forecast_times= forecast_times[-24:] #we only care for the last 24 elements

# Get the upper and lower bounds of the prediction intervals as a numpy array
prediction_intervals = pred2_ci.values
prediction_intervals= prediction_intervals[-24:] #we only care for the last 24 elements

# Generate 10 random scenarios around the forecast values
num_scenarios = 10
np.random.seed(0) #the thesis scenarios are saved in data/thesis_runs, a new draw gives different scenarios
scenarios = np.zeros((num_scenarios, forecast_values.shape[0]))
for i in range(num_scenarios):
    scenarios[i, :] = np.random.normal(forecast_values, rmse, size=forecast_values.shape[0])
    
# Create a dataframe to store the forecast values and intervals
df = pd.DataFrame(columns=['forecast', 'lower_interval', 'upper_interval'])

# Plot the forecast values and prediction intervals
plt.plot(forecast_times, forecast_values, label='Forecast')
plt.fill_between(forecast_times, prediction_intervals[:, 0], prediction_intervals[:, 1], alpha=0.5, label='Prediction Interval')

# Plot the scenarios
for i in range(num_scenarios):
    plt.plot(forecast_times, scenarios[i, :], linestyle='--', alpha=0.5)

plt.legend()
plt.xlim(forecast_times[0], forecast_times[-1])
plt.savefig(os.path.join(RESULTS, 'scenarios.png'), bbox_inches='tight')
plt.close()

# Save the forecast and the scenarios
pd.DataFrame({'scenario 0': forecast_values}).to_excel(os.path.join(RESULTS, 'predicted_mean.xlsx'))
pd.DataFrame(scenarios.T, columns=['scenario'+str(i) for i in range(num_scenarios)]).to_excel(os.path.join(RESULTS, 'scenarios_new.xlsx'))
print('DataFrame is written to Excel File successfully.')