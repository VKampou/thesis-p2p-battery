"""Run the thesis scripts in order; everything is written to results/.

    python reproduce.py

The scripts in src/ can also be run one by one (for example in Spyder):
    src/Deterministic_Executive.py   Section 6.4  deterministic battery dispatch
    src/Scenarios.py                 Section 6.5  SARIMA forecast and scenarios
    src/Executive.py                 Sections 6.6-6.7  stochastic model, MUFs and realization
"""

import os
import runpy
import sys

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, SRC)

for script in ["Deterministic_Executive.py", "Scenarios.py", "Executive.py"]:
    print("\n===== " + script, flush=True)
    runpy.run_path(os.path.join(SRC, script), run_name="__main__")
