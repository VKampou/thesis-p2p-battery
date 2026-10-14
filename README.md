# Optimal scheduling of prosumer batteries for savings and P2P market participation

Reproducible code for the diploma thesis

> **Βέλτιστος Προγραμματισμός της Λειτουργίας των Μπαταριών των Prosumers για Εξοικονόμηση και Συμμετοχή στις Peer-to-Peer Αγορές**
> Vasileios G. Kampourakis — National Technical University of Athens, School of ECE, Electric Power Division
> Supervisor: Prof. G. Korres · Approved 9 March 2023 · [thesis PDF](thesis/Kampourakis_Vasileios_Thesis.pdf) · [presentation](thesis/Thesis_Presentation.pptx)

A prosumer with a PV system and a home battery (13 kWh, 7 kW, η = 0.9) trades energy in a peer-to-peer
market for the next time step. Its load is uncertain, so a SARIMA model forecasts it and generates
Monte Carlo scenarios; a two-stage stochastic MILP then decides how much to trade at t₀. Solving it for
a range of P2P prices λₙ gives the prosumer's **Marginal Utility Function (MUF)** — a bid curve a P2P
platform can use to clear the market.

## Quick start

Requires Python 3.12 (3.10+ should work). Clone the repository, then from its folder:

**Windows (PowerShell or cmd)**

```bash
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python reproduce.py
```

**Linux / macOS**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python reproduce.py
```

Everything is written to `results/` (figures and Excel tables). A full run takes about 5 minutes.
`reproduce.py` simply runs the three scripts below in order; each can also be run on its own
(e.g. in Spyder, cell by cell):

| Script | Thesis section | What it does |
|---|---|---|
| `src/Deterministic_Executive.py` | 6.4 | battery dispatch with known load and prices, daily cost with/without battery |
| `src/Scenarios.py` | 6.5 | SARIMA(3,0,1)x(2,1,1,24) forecast of the next day and load scenarios |
| `src/Executive.py` | 6.6–6.7 | stochastic model for every t₀, initial charge and tariff → MUFs; realization comparison |

The model functions live in `src/Determenistic_Model_Generator.py` and
`src/Stohastic_Model_Generator.py`, and the plots in `src/Plots.py`.

> **Windows tips.** Use `py` rather than `python`: on many PCs `python` opens the Microsoft Store
> instead. If `pip install` fails with *"No such file or directory … pyomo …"*, the folder path is too
> long for Windows — clone into a short path such as `C:\thesis` or
> [enable long paths](https://pip.pypa.io/warnings/enable-long-paths).

The free HiGHS solver is used (installed by pip, no licence needed); the thesis used Gurobi, which
gives the same optima (pass `solver='gurobi'` to the model functions if you have a licence).
To rerun the slow AIC search over SARIMA orders, set `RUN_GRID_SEARCH = True` in `src/Scenarios.py`.

## Repository layout

```
src/                 the thesis scripts, with only the fixes needed to run and reproduce the results
original_code/       the recovered scripts, unmodified (compare with src/ to see every change)
data/raw/            inputs: 24 h prices/load, 2018 load history (Jan–Mar), stochastic demo data
data/thesis_runs/    the exact prices, scenarios and realization files the thesis figures were made from
thesis/              thesis PDF, presentation, flowchart, and the original figures (thesis/figures/)
results/             output of the reproduction (committed so it can be browsed)
```

## Reproduction status

See [REPRODUCTION.md](REPRODUCTION.md) for the figure-by-figure comparison.

| Section | Thesis | Reproduced |
|---|---|---|
| 6.4 Daily cost, no battery / battery (Fig. 15) | 8.80 € / 2.90 € | 8.80 € / 2.90 € (actual bill 5.85 €, see report) |
| 6.5 Next-day forecast | `predicted_mean.xlsx` | within 0.006 kWh, MAPE 3.97 % |
| 6.6 MUFs (Figs. 21–36) | 30 curves | same shapes and levels |
| 6.7 Cost gap stochastic vs perfect information (Fig. 38) | ≈13 % | 13.08 % → 13.42 %, identical to the saved values |

## Model conventions recovered from the thesis runs

The surviving code is a snapshot from about a month before the final version
(`original_code/1_README.txt`). `src/` keeps that code and its structure, and changes only what is
needed; the missing pieces were reconstructed from Chapter 5 and pinned down by matching the saved
thesis outputs. Run `git diff --no-index original_code src` to see every change.

- **Prices are in €/kWh.** Grid buy price λ_tb = 1.15·MCP, grid sell price λ_ts = 0.85·MCP
  (the old code used ±30 €/MWh). Future P2P prices equal the MCP.
- **λₙ grid:** 10 values between λ_ts and λ_tb, the end points pulled 1 % inside the interval.
- **Tariff:** 30 % of the MCP, charged on imported energy only.
- **Horizon:** from t₀ to the end of the day (24 − t₀ steps), 10 equiprobable load scenarios.
- **Battery:** C_min = 0, discharge power limited to P_N·η = 6.3 kW, and the end-of-day rule of the
  original code (`C[last] = C_initial + discharge[last]`). The thesis' eq. 5.11 (C_end = C_initial)
  gives costs about 0.01 € lower; the code's rule reproduces the saved values exactly.
- **Big-M:** the original `1e27` constants made the solver accept binaries of 0.999999999,
  which leaves ~1e17 kWh of slack and an unbounded-looking result. A big-M of 1000 kWh is used
  instead, and imported/exported energy are kept non-negative.
- **Scenarios:** the stochastic model takes the SARIMA scenarios as input (the old version drew its
  own Gaussian noise). The thesis' scenario sets are saved in `data/thesis_runs/` and used by
  `Executive.py`; `Scenarios.py` can draw new ones.
- **Forecast day:** the realization is the load of **2018-03-03**; the SARIMA model is trained on the
  history up to 2018-03-02 23:00.

## License

The code and data are released under the [MIT License](LICENSE). The thesis documents in `thesis/`
remain under the author's copyright: non-commercial, educational or research use is permitted with
attribution (see the thesis copyright page).
