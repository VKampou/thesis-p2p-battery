"""Two-stage stochastic model of the prosumer (thesis Section 5.3, eqs. 5.8-5.20).

The first-stage decision is the energy p_n^p2p traded in the P2P market at the
step t0 for a given P2P price lambda_n. Everything else (battery dispatch,
grid purchases/sales, future P2P trades) is decided per load scenario w.
Solving for several lambda_n values gives the Marginal Utility Function (MUF).

Sign convention (thesis 6.6.1): traded energy is positive when the prosumer
buys and negative when it sells.
"""

from dataclasses import dataclass

import numpy as np
import pyomo.environ as pyo


@dataclass
class Battery:
    c_max: float = 13.0      # kWh
    c_min: float = 0.0       # kWh
    p_nominal: float = 7.0   # kW
    efficiency: float = 0.9


@dataclass
class Prices:
    grid_buy_markup: float = 1.15   # lambda_tb = 1.15 * MCP
    grid_sell_markdown: float = 0.85  # lambda_ts = 0.85 * MCP
    tariff: float = 0.0             # c_t = tariff * MCP on imported energy only


def lambda_grid(mcp_t0, prices=Prices(), n=10):
    """P2P prices between lambda_ts and lambda_tb at t0, spaced like the thesis runs.

    The end points are pulled 1% inside the interval so lambda_n never equals a
    grid price (this reproduces the lambda values in Realization-forecast costs.xlsx).
    """
    lt_s = prices.grid_sell_markdown * mcp_t0
    lt_b = prices.grid_buy_markup * mcp_t0
    values = []
    for i in range(n):
        if i == 0:
            values.append(lt_s * 1.01)
        elif i == n - 1:
            values.append(lt_b * 0.99)
        else:
            values.append(lt_s + i * (lt_b - lt_s) / n)
    return values


def build_model(mcp, scenarios, c_initial, battery=Battery(), prices=Prices(), big_m=None,
                end_rule="code"):
    """Build the stochastic model over the horizon t0..end.

    mcp: day-ahead prices for the horizon, mcp[0] is the price at t0.
    scenarios: array (T, W) of load scenarios for the same horizon.
    """
    mcp = np.asarray(mcp, dtype=float)
    scenarios = np.asarray(scenarios, dtype=float)
    if scenarios.ndim == 1:
        scenarios = scenarios[:, None]
    T, W = scenarios.shape
    b, E = battery, battery.efficiency
    # Big-M only has to exceed any physical flow; the original 1e27 broke the solver numerically.
    if big_m is None:
        big_m = float(scenarios.max() + 2 * b.p_nominal) * 10

    m = pyo.ConcreteModel()
    m.T = pyo.RangeSet(0, T - 1)
    m.W = pyo.RangeSet(0, W - 1)
    weight = 1.0 / W

    m.lambda_n = pyo.Param(mutable=True, initialize=mcp[0])
    m.p2p_t0 = pyo.Var(domain=pyo.Reals)  # first-stage decision

    m.charge = pyo.Var(m.T, m.W, bounds=(0, b.p_nominal))
    m.discharge = pyo.Var(m.T, m.W, bounds=(0, b.p_nominal))
    m.soc = pyo.Var(m.T, m.W, bounds=(b.c_min, b.c_max))      # opening capacity of step t
    m.u = pyo.Var(m.T, m.W, domain=pyo.Binary)                # 1 = charging
    m.bought = pyo.Var(m.T, m.W, domain=pyo.NonNegativeReals)
    m.sold = pyo.Var(m.T, m.W, domain=pyo.NonNegativeReals)
    m.p2p = pyo.Var(m.T, m.W, domain=pyo.Reals)               # future P2P trades (t > t0)
    m.imported = pyo.Var(m.T, m.W, domain=pyo.NonNegativeReals)
    m.exported = pyo.Var(m.T, m.W, domain=pyo.NonNegativeReals)
    m.g = pyo.Var(m.T, m.W, domain=pyo.Binary)                # 1 = importing

    def net_demand(m, t, w):
        return scenarios[t, w] + m.charge[t, w] - m.discharge[t, w]

    # (5.9)-(5.11) battery state, with the end-of-horizon state equal to the initial one
    m.soc_start = pyo.Constraint(m.W, rule=lambda m, w: m.soc[0, w] == c_initial)
    m.soc_balance = pyo.Constraint(
        m.T, m.W, rule=lambda m, t, w: pyo.Constraint.Skip if t == 0 else
        m.soc[t, w] == m.soc[t - 1, w] + m.charge[t - 1, w] * E - m.discharge[t - 1, w] / E)
    if end_rule == "thesis":   # eq. 5.11: the battery ends the horizon where it started
        m.soc_end = pyo.Constraint(
            m.W, rule=lambda m, w:
            m.soc[T - 1, w] + m.charge[T - 1, w] * E - m.discharge[T - 1, w] / E == c_initial)
    elif end_rule == "code":   # the recovered script's version
        m.soc_end = pyo.Constraint(
            m.W, rule=lambda m, w: m.soc[T - 1, w] == c_initial + m.discharge[T - 1, w])
    m.no_overcharge = pyo.Constraint(
        m.T, m.W, rule=lambda m, t, w: m.soc[t, w] + m.charge[t, w] * E <= b.c_max)
    m.no_overdischarge = pyo.Constraint(
        m.T, m.W, rule=lambda m, t, w: m.soc[t, w] - m.discharge[t, w] / E >= b.c_min)

    # (5.12)-(5.13) power limits and no simultaneous charge/discharge
    m.only_charge = pyo.Constraint(
        m.T, m.W, rule=lambda m, t, w: m.charge[t, w] <= m.u[t, w] * b.p_nominal)
    # as in the original code, discharge power is rated on the grid side (P_N * E)
    m.only_discharge = pyo.Constraint(
        m.T, m.W, rule=lambda m, t, w: m.discharge[t, w] <= (1 - m.u[t, w]) * b.p_nominal * E)

    # (5.14)-(5.15) energy balance between traded and physical flows
    def balance(m, t, w):
        traded = m.p2p_t0 if t == 0 else m.p2p[t, w]
        return traded + m.bought[t, w] - m.sold[t, w] == net_demand(m, t, w)
    m.balance = pyo.Constraint(m.T, m.W, rule=balance)
    m.no_p2p_slot_t0 = pyo.Constraint(m.W, rule=lambda m, w: m.p2p[0, w] == 0)

    # (5.16)-(5.20) split physical import/export; grid trades cover only physical needs
    m.physical = pyo.Constraint(
        m.T, m.W, rule=lambda m, t, w: net_demand(m, t, w) == m.imported[t, w] - m.exported[t, w])
    m.import_on = pyo.Constraint(m.T, m.W, rule=lambda m, t, w: m.imported[t, w] <= m.g[t, w] * big_m)
    m.export_on = pyo.Constraint(m.T, m.W, rule=lambda m, t, w: m.exported[t, w] <= (1 - m.g[t, w]) * big_m)
    m.buy_cap = pyo.Constraint(m.T, m.W, rule=lambda m, t, w: m.bought[t, w] <= m.imported[t, w])
    m.sell_cap = pyo.Constraint(m.T, m.W, rule=lambda m, t, w: m.sold[t, w] <= m.exported[t, w])

    # (5.8) objective: first-stage P2P cost + expected grid, tariff and future P2P costs
    lt_b = prices.grid_buy_markup * mcp
    lt_s = prices.grid_sell_markdown * mcp
    tariff = prices.tariff * mcp

    def expected_cost(m):
        second_stage = sum(
            weight * (lt_b[t] * m.bought[t, w] - lt_s[t] * m.sold[t, w] + tariff[t] * m.imported[t, w]
                      + (mcp[t] * m.p2p[t, w] if t > 0 else 0))
            for t in m.T for w in m.W)
        return m.lambda_n * m.p2p_t0 + second_stage
    m.cost = pyo.Objective(rule=expected_cost, sense=pyo.minimize)
    return m


def solve(model, solver="appsi_highs"):
    result = pyo.SolverFactory(solver).solve(model)
    status = str(result.solver.termination_condition)
    if status != "optimal":
        raise RuntimeError(f"solver finished with status {status}")
    return model


def muf(mcp, scenarios, c_initial, prices=Prices(), battery=Battery(), n=10, solver="appsi_highs",
        end_rule="code"):
    """Solve the model for every lambda_n and return the MUF as (lambda_n, p2p_t0, expected cost) rows."""
    model = build_model(mcp, scenarios, c_initial, battery, prices, end_rule=end_rule)
    rows = []
    for lam in lambda_grid(mcp[0], prices, n):
        model.lambda_n = lam
        solve(model, solver)
        rows.append((lam, pyo.value(model.p2p_t0), pyo.value(model.cost)))
    return rows
