# Reproduction report

Every Chapter 6 result was rebuilt with `python reproduce.py` (HiGHS solver, package
versions in `requirements.txt`) and compared with the figures in the thesis
(`thesis/figures/`) and the saved thesis run files (`data/thesis_runs/`).

## Summary

| Section | Result in the thesis | Reproduced | Match |
|---|---|---|---|
| 6.4 Battery dispatch (Fig. 14) | charge/discharge pattern | same hours and powers, except the small 0.44 kW top-up at 06:00 instead of 05:00 (note 4) | ✅ |
| 6.4 Daily cost (Fig. 15) | 8.80 € without, ≈2.90 € with battery | 8.80 € / 2.90 € | ✅ exact, but see note 1 |
| 6.5 SARIMA order | (3,0,1)×(2,1,1,24) by AIC | refitted with the same order | ✅ |
| 6.5 Forecast (Fig. 18) | `predicted_mean.xlsx` | max difference 0.006 kWh, MAPE 3.97 % | ✅ (optimizer version) |
| 6.5 Scenarios (Fig. 19) | 10 Monte Carlo scenarios | the saved thesis scenarios are used | ✅ (random draw, see note 2) |
| 6.6 MUF t₀=0, C=7 (Fig. 21) | sells ≈4.5 kWh at every price | −4.31 kWh at every price | ✅ |
| 6.6 MUFs (Figs. 22–36) | 30 curves | same shape and levels; some intermediate points differ | ✅ qualitative, see note 2 |
| 6.7 Realization vs forecast MUF (Fig. 37) | 0.98 kWh flat vs 0.94→0.885 kWh | 0.983 flat vs 0.94→0.885 kWh | ✅ exact |
| 6.7 Cost error (Fig. 38) | ≈13 %, under 0.5 % spread | 13.08 % → 13.42 %; costs equal the saved values to 1e-15 | ✅ exact |

## Notes

1. **Fig. 15 counts the battery twice.** The deterministic objective in
   `Determenistic_Model_Generator.py` prices `charge` and `discharge` on top of `bought_power`, which already
   contains them. The 2.90 € plotted in Fig. 15 is that objective value; the actual energy bill with
   the battery is **5.85 €**. The true saving is 2.95 € (34 %), not 5.9 € (67 %). The dispatch
   itself is unaffected (both versions charge in the same cheap hours), so Fig. 14 stands.
   `Deterministic_Executive.py` prints both numbers.
2. **Scenarios are random.** The thesis kept one scenario set per time step (`scenarios_0/4/19.xlsx`)
   and the reproduction uses those. Fig. 37/38 were produced from exactly these files (they match
   to machine precision). Figs. 22–36 show the same behaviour but a few intermediate points differ by
   up to ≈0.5 kWh (e.g. t₀=19, C=7, tariff), which is consistent with those figures having been made
   from an earlier draw of scenarios that was not saved. `Scenarios.py` draws a new set
   (`results/scenarios_new.xlsx`, shown in `results/scenarios.png`), so Fig. 19 matches in kind
   but not line by line.
3. **Not presented in the thesis:** `Realization-forecast costs.xlsx` contains a second block of
   ten rows that does not correspond to the tariff case or to any figure; it is left out.
4. **Solver:** the thesis used Gurobi; HiGHS reaches the same optimal costs. Where the optimum is
   not unique (several trade quantities with equal cost), the two solvers may pick different points.

## Section 6.4 — deterministic model

| | Thesis | Reproduced |
|---|---|---|
| Fig. 14 dispatch | ![](thesis/figures/fig14_dispatch.png) | ![](results/fig14_dispatch.png) |
| Fig. 15 cost | ![](thesis/figures/fig15_cost.png) | printed by the script: 8.80 € without battery, 2.90 € objective with battery (actual bill 5.85 €) |

## Section 6.5 — forecasting

| | Thesis | Reproduced |
|---|---|---|
| Fig. 17 diagnostics | ![](thesis/figures/fig17_diagnostics.png) | ![](results/diagnostics.png) |
| Fig. 18 forecast | ![](thesis/figures/fig18_forecast.png) | ![](results/forecast.png) |
| Fig. 19 scenarios | ![](thesis/figures/fig19_scenarios.png) | ![](results/scenarios.png) |

## Section 6.6 — Marginal Utility Functions

Both columns: tariff 30 % first, then no tariff. The values are in `results/MUF_results.xlsx`.

| Case | Thesis | Reproduced |
|---|---|---|
| Fig. 22 — t₀=0, C=1 kWh | ![](thesis/figures/muf_t0_0_C_1_tariff30.png) ![](thesis/figures/muf_t0_0_C_1_tariff0.png) | ![](results/MUF_t0_0_C_1_tariff30.png) ![](results/MUF_t0_0_C_1_tariff0.png) |
| Fig. 23 — t₀=0, C=5 kWh | ![](thesis/figures/muf_t0_0_C_5_tariff30.png) ![](thesis/figures/muf_t0_0_C_5_tariff0.png) | ![](results/MUF_t0_0_C_5_tariff30.png) ![](results/MUF_t0_0_C_5_tariff0.png) |
| Fig. 24 — t₀=0, C=7 kWh | ![](thesis/figures/muf_t0_0_C_7_tariff30.png) ![](thesis/figures/muf_t0_0_C_7_tariff0.png) | ![](results/MUF_t0_0_C_7_tariff30.png) ![](results/MUF_t0_0_C_7_tariff0.png) |
| Fig. 25 — t₀=0, C=9 kWh | ![](thesis/figures/muf_t0_0_C_9_tariff30.png) ![](thesis/figures/muf_t0_0_C_9_tariff0.png) | ![](results/MUF_t0_0_C_9_tariff30.png) ![](results/MUF_t0_0_C_9_tariff0.png) |
| Fig. 26 — t₀=0, C=13 kWh | ![](thesis/figures/muf_t0_0_C_13_tariff30.png) ![](thesis/figures/muf_t0_0_C_13_tariff0.png) | ![](results/MUF_t0_0_C_13_tariff30.png) ![](results/MUF_t0_0_C_13_tariff0.png) |
| Fig. 27 — t₀=4, C=1 kWh | ![](thesis/figures/muf_t0_4_C_1_tariff30.png) ![](thesis/figures/muf_t0_4_C_1_tariff0.png) | ![](results/MUF_t0_4_C_1_tariff30.png) ![](results/MUF_t0_4_C_1_tariff0.png) |
| Fig. 28 — t₀=4, C=5 kWh | ![](thesis/figures/muf_t0_4_C_5_tariff30.png) ![](thesis/figures/muf_t0_4_C_5_tariff0.png) | ![](results/MUF_t0_4_C_5_tariff30.png) ![](results/MUF_t0_4_C_5_tariff0.png) |
| Fig. 29 — t₀=4, C=7 kWh | ![](thesis/figures/muf_t0_4_C_7_tariff30.png) ![](thesis/figures/muf_t0_4_C_7_tariff0.png) | ![](results/MUF_t0_4_C_7_tariff30.png) ![](results/MUF_t0_4_C_7_tariff0.png) |
| Fig. 30 — t₀=4, C=9 kWh | ![](thesis/figures/muf_t0_4_C_9_tariff30.png) ![](thesis/figures/muf_t0_4_C_9_tariff0.png) | ![](results/MUF_t0_4_C_9_tariff30.png) ![](results/MUF_t0_4_C_9_tariff0.png) |
| Fig. 31 — t₀=4, C=13 kWh | ![](thesis/figures/muf_t0_4_C_13_tariff30.png) ![](thesis/figures/muf_t0_4_C_13_tariff0.png) | ![](results/MUF_t0_4_C_13_tariff30.png) ![](results/MUF_t0_4_C_13_tariff0.png) |
| Fig. 32 — t₀=19, C=1 kWh | ![](thesis/figures/muf_t0_19_C_1_tariff30.png) ![](thesis/figures/muf_t0_19_C_1_tariff0.png) | ![](results/MUF_t0_19_C_1_tariff30.png) ![](results/MUF_t0_19_C_1_tariff0.png) |
| Fig. 33 — t₀=19, C=5 kWh | ![](thesis/figures/muf_t0_19_C_5_tariff30.png) ![](thesis/figures/muf_t0_19_C_5_tariff0.png) | ![](results/MUF_t0_19_C_5_tariff30.png) ![](results/MUF_t0_19_C_5_tariff0.png) |
| Fig. 34 — t₀=19, C=7 kWh | ![](thesis/figures/muf_t0_19_C_7_tariff30.png) ![](thesis/figures/muf_t0_19_C_7_tariff0.png) | ![](results/MUF_t0_19_C_7_tariff30.png) ![](results/MUF_t0_19_C_7_tariff0.png) |
| Fig. 35 — t₀=19, C=9 kWh | ![](thesis/figures/muf_t0_19_C_9_tariff30.png) ![](thesis/figures/muf_t0_19_C_9_tariff0.png) | ![](results/MUF_t0_19_C_9_tariff30.png) ![](results/MUF_t0_19_C_9_tariff0.png) |
| Fig. 36 — t₀=19, C=13 kWh | ![](thesis/figures/muf_t0_19_C_13_tariff30.png) ![](thesis/figures/muf_t0_19_C_13_tariff0.png) | ![](results/MUF_t0_19_C_13_tariff30.png) ![](results/MUF_t0_19_C_13_tariff0.png) |

## Section 6.7 — realization and model performance

| | Thesis | Reproduced |
|---|---|---|
| Fig. 37 | ![](thesis/figures/fig37_realization.png) ![](thesis/figures/fig37_forecast.png) | ![](results/MUF_realization.png) ![](results/MUF_forecast.png) |
| Fig. 38 | ![](thesis/figures/fig38_cost_error.png) | ![](results/realization_error.png) |

The numbers are in `results/Realization-forecast costs.xlsx`; the thesis values are in
`data/thesis_runs/Realization-forecast costs.xlsx`.
