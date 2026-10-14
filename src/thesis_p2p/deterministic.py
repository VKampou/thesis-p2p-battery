"""Deterministic battery dispatch against day-ahead prices (thesis Sections 5.2 and 6.4).

Energy is bought and sold at the same price (the market clearing price), and the
load is known. Port of the original Determenistic_Model_Generator.py.
"""

import pandas as pd
import pyomo.environ as pyo

from .stochastic import Battery


def solve_dispatch(mcp, load, c_initial=10.0, battery=Battery(), solver="appsi_highs"):
    mcp = list(mcp)
    load = list(load)
    T = len(mcp)
    b, E = battery, battery.efficiency

    m = pyo.ConcreteModel()
    m.T = pyo.RangeSet(0, T - 1)
    m.soc = pyo.Var(m.T, bounds=(b.c_min, b.c_max))
    m.charge = pyo.Var(m.T, bounds=(0, b.p_nominal))
    m.discharge = pyo.Var(m.T, bounds=(0, b.p_nominal))
    m.bought = pyo.Var(m.T)  # negative = sold back to the grid
    m.u = pyo.Var(m.T, domain=pyo.Binary)

    # Objective exactly as in the thesis code: charge and discharge are priced on top of
    # `bought`, which already contains them, so battery flows are counted twice.
    # `true_cost` below reports the actual energy bill.
    m.cost = pyo.Objective(
        expr=sum(mcp[t] * (m.charge[t] + m.bought[t] - m.discharge[t]) for t in m.T),
        sense=pyo.minimize)

    m.no_overcharge = pyo.Constraint(m.T, rule=lambda m, t: m.charge[t] <= (b.c_max - m.soc[t]) / E)
    m.no_overdischarge = pyo.Constraint(m.T, rule=lambda m, t: m.discharge[t] <= m.soc[t] * E)
    m.no_negative_price_discharge = pyo.Constraint(
        m.T, rule=lambda m, t: m.discharge[t] == 0 if mcp[t] <= 0 else pyo.Constraint.Skip)
    m.soc_balance = pyo.Constraint(
        m.T, rule=lambda m, t: m.soc[t] == c_initial if t == 0 else
        m.soc[t] == m.soc[t - 1] + m.charge[t - 1] * E - m.discharge[t - 1] / E)
    m.balance = pyo.Constraint(
        m.T, rule=lambda m, t: m.bought[t] == m.charge[t] + load[t] - m.discharge[t])
    m.only_charge = pyo.Constraint(m.T, rule=lambda m, t: m.charge[t] <= m.u[t] * b.p_nominal / E)
    m.only_discharge = pyo.Constraint(
        m.T, rule=lambda m, t: m.discharge[t] <= (1 - m.u[t]) * b.p_nominal * E)
    m.soc_end = pyo.Constraint(expr=m.soc[T - 1] == c_initial + m.discharge[T - 1])

    pyo.SolverFactory(solver).solve(m)

    result = pd.DataFrame({
        "time": range(T), "MCP": mcp, "p_load": load,
        "bought_power": [m.bought[t].value for t in m.T],
        "charge_power": [m.charge[t].value for t in m.T],
        "discharge_power": [m.discharge[t].value for t in m.T],
        "opening_capacity": [m.soc[t].value for t in m.T],
    })
    summary = {
        "cost_without_battery": sum(p * l for p, l in zip(mcp, load)),
        "objective_with_battery": pyo.value(m.cost),        # the value plotted in thesis Fig. 15
        "true_cost_with_battery": float((result.MCP * result.bought_power).sum()),
    }
    return result, summary
