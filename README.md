# Optimal scheduling of prosumer batteries for savings and P2P market participation

Code for the diploma thesis

> **Βέλτιστος Προγραμματισμός της Λειτουργίας των Μπαταριών των Prosumers για Εξοικονόμηση και Συμμετοχή στις Peer-to-Peer Αγορές**
> Vasileios G. Kampourakis — National Technical University of Athens, School of Electrical and Computer Engineering, Electric Power Division
> Supervisor: Prof. G. Korres · Approved 9 March 2023 · [thesis PDF](thesis/Kampourakis_Vasileios_Thesis.pdf) · [presentation](thesis/Thesis_Presentation.pptx)

## Thesis summary

In a peer-to-peer (P2P) energy market, participants buy and sell energy directly with each other
for each upcoming time step, without an intermediary. Prosumers, consumers who also produce energy
(e.g. with rooftop PV) and often own a battery, are central to such markets. Before each market
clearing, every participant must state how much energy it wants to buy or sell, and that decision
directly determines how much it gains from taking part.

The thesis proposes a practical way for a prosumer with a home battery (13 kWh, 7 kW, efficiency 0.9)
to make this decision:

1. **Deterministic battery dispatch.** With known prices and load, a mixed-integer model schedules
   charging and discharging over a day. It charges when energy is cheap and discharges when it is
   expensive, and it lowers the daily energy cost considerably.
2. **Load forecasting and scenarios.** The prosumer's net load is uncertain, so a SARIMA(3,0,1)×(2,1,1,24)
   model is trained on historical hourly data and used to generate a set of load scenarios for the
   next day.
3. **Two-stage stochastic optimisation.** The first-stage decision is the energy traded in the P2P
   market at the next time step t₀. The second-stage decisions (battery operation, purchases from and
   sales to the grid, future trades) adapt to each scenario.
4. **Marginal Utility Function (MUF).** The problem is solved for a range of P2P prices between the
   grid's selling and buying prices. The resulting price–energy pairs form the prosumer's MUF, which
   fully describes its willingness to trade and can be used by a market operator or a blockchain
   platform to clear the market.

**Findings.** The prosumer buys when energy is cheap and sells when it is expensive. The shape of
the MUF depends strongly on the battery's initial charge, on the time step, and on whether a tariff
is charged on imported energy. Compared with the optimal decisions made with perfect knowledge of the
load, the stochastic approach gives a cost that differs by about 13 %, almost constant across P2P
prices.

## Running the code

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

Everything is written to `results/` (figures and Excel tables). A full run takes about 5–10 minutes.
`reproduce.py` runs the three scripts below in order; each can also be run on its own
(e.g. in Spyder, cell by cell):

| Script | Thesis section | What it does |
|---|---|---|
| `src/Deterministic_Executive.py` | 6.4 | battery dispatch with known load and prices, daily cost with/without battery |
| `src/Scenarios.py` | 6.5 | SARIMA forecast of the next day and load scenarios |
| `src/Executive.py` | 6.6–6.7 | stochastic model for every t₀, initial charge and tariff → MUFs; comparison with the realization |

The models are in `src/Determenistic_Model_Generator.py` and `src/Stohastic_Model_Generator.py`, the
plots in `src/Plots.py`. The free HiGHS solver is used (installed by pip); the thesis used Gurobi,
which gives the same optima (pass `solver='gurobi'` if you have a licence). To rerun the slow AIC
search over SARIMA orders, set `RUN_GRID_SEARCH = True` in `src/Scenarios.py`.

> **Windows tips.** Use `py` rather than `python`: on many PCs `python` opens the Microsoft Store
> instead. If `pip install` fails with *"No such file or directory … pyomo …"*, the folder path is too
> long for Windows. Clone into a short path such as `C:\thesis` or
> [enable long paths](https://pip.pypa.io/warnings/enable-long-paths).

## Repository layout

```
src/                 the thesis scripts
original_code/       the scripts as recovered, unmodified
data/raw/            inputs: 24 h prices and load, hourly load history Jan–Mar 2018
data/thesis_runs/    the prices, scenarios and realization files the thesis figures were made from
thesis/              thesis PDF, presentation, flowchart and the original figures (thesis/figures/)
results/             output of the code
REPRODUCTION.md      figure-by-figure comparison of the results with the thesis
```

## License

The code and data are released under the [MIT License](LICENSE). The thesis documents in `thesis/`
remain under the author's copyright: non-commercial, educational or research use is permitted with
attribution (see [thesis/README.md](thesis/README.md)).

## Note on the reproduction (October 2026)

The thesis was completed in March 2023 (final PDF June 2023). Part of the final code was lost; the
surviving scripts are about a month older than the final version (see `original_code/1_README.txt`).
In October 2026 the results of Chapter 6 were reproduced from those scripts, and they match the
thesis: the realization comparison (Figs. 37–38) agrees with the saved thesis values to machine
precision, and the other figures match in shape and values (see [REPRODUCTION.md](REPRODUCTION.md)).

The modifications needed (run `git diff --no-index original_code src` to see every line):

- **Environment:** relative file paths instead of local folders, HiGHS instead of Gurobi, figures
  saved to `results/`, and small fixes for current versions of pandas and statsmodels.
- **Final model conventions,** recovered by matching the saved thesis outputs: prices in €/kWh with
  grid buy/sell prices of 1.15·MCP and 0.85·MCP (the older code used ±30 €/MWh), a 30 % tariff on
  imported energy, and 10 P2P prices per MUF.
- **Scenarios:** the stochastic model takes the SARIMA scenarios as input. The older version
  generated its own random noise.
- **Big-M:** the constants of `1e27` made the solver return meaningless results and were reduced
  to 1000; imported and exported energy were made non-negative.
- **Forecast day:** the SARIMA model is trained up to 2 March 2018 and forecasts 3 March 2018, the
  day used as the realization in the thesis.
- **Lost part rebuilt:** the loop in `Executive.py` over time steps, initial charges and tariffs, and
  the comparison with the realization.
- **Correction:** the deterministic objective counts the battery's charging and discharging twice,
  so the cost with the battery plotted in Fig. 15 (2.90 €) is lower than the actual bill (5.85 €).
  The battery dispatch itself is not affected. The script now prints both values.
