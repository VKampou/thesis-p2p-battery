"""Figures in the style of thesis Chapter 6 (figure numbers refer to the thesis)."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HOURS = [f"{h:02d}:00" for h in range(24)]


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def price_and_load(result, out_dir):
    for column, label, name in [("MCP", "Τιμή (€/kWh)", "fig12_mcp.png"),
                                ("p_load", "Φορτίο (kW)", "fig13_load.png")]:
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(result.time, result[column], marker="o")
        ax.set_xticks(result.time, HOURS, rotation=90)
        ax.set_ylabel(label)
        ax.grid(alpha=0.4)
        _save(fig, out_dir / name)


def dispatch(result, path):
    fig, ax = plt.subplots(figsize=(6, 6))
    x = np.arange(len(result))
    ax.bar(x - 0.2, result.charge_power, 0.4, label="charge_power")
    ax.bar(x + 0.2, result.discharge_power, 0.4, label="discharge_power")
    ax.set_xticks(x, HOURS, rotation=90)
    ax.set_ylabel("Ισχύς (kW)")
    ax.set_title("Dispatch")
    ax.legend()
    ax.grid(axis="y", alpha=0.4)
    _save(fig, path)


def cost_comparison(summary, path):
    fig, ax = plt.subplots(figsize=(6, 5))
    labels = ["Χωρίς Μπαταρία", "Με Μπαταρία\n(objective, as in thesis)", "Με Μπαταρία\n(actual bill)"]
    values = [summary["cost_without_battery"], summary["objective_with_battery"],
              summary["true_cost_with_battery"]]
    bars = ax.bar(labels, values, color=["tab:blue", "tab:orange", "tab:green"])
    ax.bar_label(bars, fmt="%.2f €")
    ax.set_ylabel("Συνολικό Κόστος (€)")
    ax.set_title("Σύγκριση Κόστους Ενέργειας με και χωρίς Μπαταρία")
    _save(fig, path)


def load_history(series, path, days=15):
    fig, ax = plt.subplots(figsize=(12, 4.5))
    series.iloc[:days * 24].plot(ax=ax)
    ax.set_ylabel("Φορτίο (kWh)")
    ax.grid(alpha=0.4)
    _save(fig, path)


def diagnostics(results, path):
    fig = results.plot_diagnostics(figsize=(14, 10))
    _save(fig, path)


def forecast(mean, ci, realization, path):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(mean))
    ax.plot(x, realization, label="Realization", color="tab:blue")
    ax.plot(x, mean.values, label="Forecast", color="tab:orange")
    ax.fill_between(x, ci.iloc[:, 0], ci.iloc[:, 1], color="k", alpha=0.1, label="95% CI")
    ax.set_xticks(x, HOURS, rotation=90)
    ax.set_ylabel("Φορτίο (kWh)")
    ax.legend()
    ax.grid(alpha=0.4)
    _save(fig, path)


def scenarios(mean, ci, scenario_frame, path):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(mean))
    ax.fill_between(x, ci.iloc[:, 0], ci.iloc[:, 1], alpha=0.3, label="Prediction interval")
    ax.plot(x, mean.values, color="k", label="Forecast")
    for column in scenario_frame:
        ax.plot(x, scenario_frame[column].values, linestyle="--", alpha=0.7)
    ax.set_xticks(x, HOURS, rotation=90)
    ax.set_ylabel("Φορτίο (kWh)")
    ax.legend()
    _save(fig, path)


def _muf_axes(ax, rows, lt_s, lt_b, title):
    lam = [r[0] for r in rows]
    energy = [r[1] for r in rows]
    ax.plot(energy, lam, "-o", ms=16, alpha=0.7, mfc="orange")
    ax.axhline(lt_s, color="k", linestyle="--")
    ax.axhline(lt_b, color="k", linestyle="--")
    ax.axvline(0, color="r", linestyle="--")
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("Ενέργεια που Επιθυμεί να Ανταλλάξει ο Prosumer (kWh)")
    ax.set_ylabel("Τιμή στην P2P αγορά (€/kWh)")
    ax.grid(alpha=0.4)


def muf_pair(rows_tariff, rows_no_tariff, lt_s, lt_b, t0, c_initial, path):
    """Thesis Figs. 22-36: tariff of 30% on the left, no tariff on the right."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    _muf_axes(axes[0], rows_tariff, lt_s, lt_b, f"MUF, t_0={t0}, C_initial={c_initial} kWh, Tariff=30%")
    _muf_axes(axes[1], rows_no_tariff, lt_s, lt_b, f"MUF, t_0={t0}, C_initial={c_initial} kWh, Tariff=0")
    _save(fig, path)


def realization_vs_forecast(rows_real, rows_forecast, lt_s, lt_b, path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharex=True)
    _muf_axes(axes[0], rows_real, lt_s, lt_b, "Realization")
    _muf_axes(axes[1], rows_forecast, lt_s, lt_b, "Forecast")
    _save(fig, path)


def cost_error(lambdas, error_pct, path, reference=None):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(lambdas, error_pct, "-o", label="reproduced")
    if reference is not None:
        ax.plot(lambdas, reference, "x", ms=10, color="k", label="thesis (saved values)")
        ax.legend()
    ax.set_xlabel("Τιμή στην P2P αγορά (€/kWh)")
    ax.set_ylabel("Σφάλμα κόστους (%)")
    ax.grid(alpha=0.4)
    _save(fig, path)
