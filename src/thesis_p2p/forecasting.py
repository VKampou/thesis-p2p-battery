"""SARIMA load forecast and Monte Carlo load scenarios (thesis Section 6.5)."""

import itertools
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm

ORDER = (3, 0, 1)
SEASONAL_ORDER = (2, 1, 1, 24)   # chosen by AIC in the thesis


def load_history(path):
    data = pd.read_excel(path)
    data["timestamp"] = pd.to_datetime(data["timestamp"])
    series = data.set_index("timestamp")["Historical Load Data"].asfreq("h")
    return series


def fit(series, order=ORDER, seasonal_order=SEASONAL_ORDER):
    model = sm.tsa.statespace.SARIMAX(series, order=order, seasonal_order=seasonal_order,
                                      enforce_stationarity=False, enforce_invertibility=False)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return model.fit(disp=False)


def aic_grid_search(series, p_values=range(0, 5), d_values=range(0, 2), q_values=range(0, 2)):
    """Grid search used to pick the SARIMA orders (slow: one fit per combination)."""
    rows = []
    for order in itertools.product(p_values, d_values, q_values):
        for seasonal in itertools.product(p_values, d_values, q_values):
            try:
                rows.append((order, seasonal + (24,), fit(series, order, seasonal + (24,)).aic))
            except Exception:
                continue
    return pd.DataFrame(rows, columns=["order", "seasonal_order", "aic"]).sort_values("aic")


def forecast_next_day(results, steps=24):
    forecast = results.get_forecast(steps)
    return forecast.predicted_mean, forecast.conf_int(alpha=0.05)


def scenarios(results, n=10, steps=24, seed=None):
    """Monte Carlo scenarios: simulate the fitted model forward from the end of the sample,
    drawing innovations from its estimated error distribution."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        np.random.seed(seed)  # statsmodels 0.15 rejects its own random_state argument under pandas 3
        sims = results.simulate(steps, anchor="end", repetitions=n)
    sims = np.asarray(sims).reshape(steps, n)
    return pd.DataFrame(sims, columns=[f"scenario{i}" for i in range(n)])
