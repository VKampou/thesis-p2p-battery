"""Rebuild every Chapter 6 result into results/.

    python -m thesis_p2p.reproduce                 # everything, using the thesis' saved scenarios
    python -m thesis_p2p.reproduce --only 6.4      # one section
    python -m thesis_p2p.reproduce --fresh-scenarios --seed 1   # draw new SARIMA scenarios instead
    python -m thesis_p2p.reproduce --grid-search   # also rerun the slow AIC search
"""

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from . import deterministic, forecasting, plots
from .stochastic import Prices, lambda_grid, muf

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
RUNS = ROOT / "data" / "thesis_runs"

FORECAST_DAY = "2018-03-03"           # realization_0.xlsx is exactly this day of the history
TIME_STEPS = (0, 4, 19)               # mid, very low and very high price (thesis 6.6.2)
INITIAL_CHARGES = (1, 5, 7, 9, 13)    # kWh
TARIFF = 0.3                          # 30% of the MCP on imported energy
SCENARIO_SEEDS = {0: 0, 4: 4, 19: 19}


def section_6_4(out):
    data = pd.read_excel(RAW / "data_deterministic.xlsx")
    result, summary = deterministic.solve_dispatch(data.MCP, data.p_load)
    result.to_csv(out / "6.4_dispatch.csv", index=False)
    plots.price_and_load(result, out)
    plots.dispatch(result, out / "fig14_dispatch.png")
    plots.cost_comparison(summary, out / "fig15_cost.png")
    return summary


def section_6_5(out, grid_search=False):
    history = forecasting.load_history(RAW / "data_set.xlsx")
    train = history[:pd.Timestamp(FORECAST_DAY) - pd.Timedelta(hours=1)]
    results = forecasting.fit(train)
    mean, ci = forecasting.forecast_next_day(results)
    realization = pd.read_excel(RUNS / "realization_0.xlsx").iloc[:, 0].values
    saved_mean = pd.read_excel(RUNS / "predicted_mean.xlsx").iloc[:, 0].values

    plots.load_history(history, out / "fig16_load_history.png")
    plots.diagnostics(results, out / "fig17_diagnostics.png")
    plots.forecast(mean, ci, realization, out / "fig18_forecast.png")
    plots.scenarios(mean, ci, pd.read_excel(RUNS / "scenarios_0.xlsx"), out / "fig19_scenarios.png")
    pd.DataFrame({"forecast": mean.values, "thesis_forecast": saved_mean, "realization": realization,
                  "ci_low": ci.iloc[:, 0].values, "ci_high": ci.iloc[:, 1].values}).to_csv(
        out / "6.5_forecast.csv", index=False)

    summary = {
        "order": str(forecasting.ORDER), "seasonal_order": str(forecasting.SEASONAL_ORDER),
        "aic": float(results.aic),
        "max_abs_diff_vs_thesis_forecast": float(np.abs(mean.values - saved_mean).max()),
        "mape_vs_realization_pct": float(np.mean(np.abs(mean.values - realization) / realization) * 100),
    }
    if grid_search:
        table = forecasting.aic_grid_search(train)
        table.to_csv(out / "6.5_aic_grid.csv", index=False)
        summary["best_by_aic"] = f"{table.iloc[0].order}x{table.iloc[0].seasonal_order}"
    return summary, results


def _horizon(t0, fresh_results=None, seed=None):
    prices = pd.read_excel(RUNS / f"prices_{t0}.xlsx").MCP.values
    if fresh_results is not None:
        scenarios = forecasting.scenarios(fresh_results, seed=seed).values[t0:]
    else:
        scenarios = pd.read_excel(RUNS / f"scenarios_{t0}.xlsx").values
    return prices, scenarios


def section_6_6(out, fresh_results=None):
    rows = []
    for t0 in TIME_STEPS:
        mcp, scenarios = _horizon(t0, fresh_results, SCENARIO_SEEDS[t0])
        lt_s, lt_b = Prices().grid_sell_markdown * mcp[0], Prices().grid_buy_markup * mcp[0]
        for c in INITIAL_CHARGES:
            with_tariff = muf(mcp, scenarios, c, prices=Prices(tariff=TARIFF))
            without = muf(mcp, scenarios, c, prices=Prices())
            plots.muf_pair(with_tariff, without, lt_s, lt_b, t0, c, out / f"muf_t0_{t0}_C_{c}.png")
            for tariff, curve in ((TARIFF, with_tariff), (0.0, without)):
                for lam, energy, cost in curve:
                    rows.append({"t0": t0, "c_initial": c, "tariff": tariff,
                                 "lambda_n": lam, "p2p_energy": energy, "expected_cost": cost})
            print(f"  MUF t0={t0} C={c} done", flush=True)
    table = pd.DataFrame(rows)
    table.to_csv(out / "6.6_muf.csv", index=False)
    return table


def section_6_7(out):
    mcp, scenarios = _horizon(0)
    realization = pd.read_excel(RUNS / "realization_0.xlsx").values
    perfect = muf(mcp, realization, 1.0)
    forecast = muf(mcp, scenarios, 1.0)
    lt_s, lt_b = Prices().grid_sell_markdown * mcp[0], Prices().grid_buy_markup * mcp[0]
    plots.realization_vs_forecast(perfect, forecast, lt_s, lt_b, out / "fig37_realization_vs_forecast.png")

    saved = pd.read_excel(RUNS / "Realization-forecast costs.xlsx", header=None).iloc[:10]
    lambdas = [r[0] for r in perfect]
    error = [(p[2] - f[2]) / p[2] * 100 for p, f in zip(perfect, forecast)]
    plots.cost_error(lambdas, error, out / "fig38_cost_error.png", reference=saved[4].values)
    table = pd.DataFrame({
        "lambda_n": lambdas, "thesis_lambda_n": saved[0].values,
        "cost_realization": [r[2] for r in perfect], "thesis_cost_realization": saved[1].values,
        "cost_forecast": [r[2] for r in forecast], "thesis_cost_forecast": saved[2].values,
        "error_pct": error, "thesis_error_pct": saved[4].values,
        "p2p_realization": [r[1] for r in perfect], "p2p_forecast": [r[1] for r in forecast]})
    table.to_csv(out / "6.7_realization.csv", index=False)
    return {
        "max_abs_cost_diff_vs_thesis": float(max(
            (table.cost_realization - table.thesis_cost_realization).abs().max(),
            (table.cost_forecast - table.thesis_cost_forecast).abs().max())),
        "error_pct_range": [float(min(error)), float(max(error))],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", choices=["6.4", "6.5", "6.6", "6.7"])
    parser.add_argument("--out", type=Path, default=ROOT / "results")
    parser.add_argument("--fresh-scenarios", action="store_true",
                        help="draw new SARIMA scenarios for 6.6 instead of the saved thesis ones")
    parser.add_argument("--grid-search", action="store_true", help="rerun the AIC grid search (slow)")
    args = parser.parse_args(argv)
    logging.getLogger("pyomo").setLevel(logging.ERROR)
    args.out.mkdir(parents=True, exist_ok=True)

    summary_path = args.out / "summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    wanted = [args.only] if args.only else ["6.4", "6.5", "6.6", "6.7"]
    sarima = None
    if "6.4" in wanted:
        print("6.4 deterministic dispatch", flush=True)
        summary["6.4"] = section_6_4(args.out)
    if "6.5" in wanted or args.fresh_scenarios and "6.6" in wanted:
        print("6.5 SARIMA forecast (about a minute)", flush=True)
        summary["6.5"], sarima = section_6_5(args.out, args.grid_search)
    if "6.6" in wanted:
        print("6.6 marginal utility functions", flush=True)
        section_6_6(args.out, sarima if args.fresh_scenarios else None)
        summary["6.6"] = {"scenarios": "fresh SARIMA draws" if args.fresh_scenarios else "saved thesis runs"}
    if "6.7" in wanted:
        print("6.7 realization vs forecast", flush=True)
        summary["6.7"] = section_6_7(args.out)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
