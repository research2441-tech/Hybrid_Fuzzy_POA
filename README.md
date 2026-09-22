# Hybrid Fuzzy-POA Microgrid Reproducibility Package

This repository provides a flat, reproducible Python implementation of the computational workflow described in the manuscript:

**Optimal Configuration Identification of Microgrids Using a Hybrid Fuzzy-Puzzle Optimization Approach for Normal and Abnormal Operations**

The implementation is designed to make the methodology auditable and repeatable. It reproduces the core workflow described in the manuscript: IEEE 33-bus radial distribution-system modelling, 3-MG and 5-MG scenarios, DE/MT/FC distributed-generation options, economic-cost/emission/voltage-deviation objectives, radial reconfiguration, fuzzy multi-objective aggregation, base-load/critical-load/fault scenarios, repeated stochastic runs, and publication-quality plotting.

## Important scope note

The uploaded manuscript does not provide every numerical constant required for exact bit-for-bit reproduction of every reported table entry. In particular, some cost/emission coefficients, comparator hyperparameters, randomized critical-load allocations, and penalty weights are not fully specified, and a few reported values are internally inconsistent. This repository therefore makes every implementation assumption explicit in `config.yaml` and keeps the original manuscript values separately in `expected_results.csv` for transparent validation.

No result is hard-coded into the optimizer.

## Flat repository layout

- `README.md` — reproducibility instructions
- `requirements.txt` — Python dependencies
- `config.yaml` — all experiment controls
- `ieee33_data.py` — IEEE 33-bus feeder, loads, branches, tie switches
- `power_flow.py` — radial backward/forward sweep solver
- `objectives.py` — economic cost, emission cost, voltage deviation, loss
- `constraints.py` — feasibility, radiality and penalty handling
- `scenarios.py` — base, critical-load and fault scenarios
- `fuzzy_poa.py` — Hybrid Fuzzy-POA optimizer
- `baseline_heuristics.py` — PSO, FPA/FFA-style, MFO and IMFO baselines
- `gradient_baseline.py` — continuous SLSQP relaxation baseline
- `run_experiments.py` — command-line experiment runner
- `statistical_analysis.py` — repeated-run statistical summaries
- `generate_figures.py` — figures for voltage, current and convergence
- `validate_results.py` — compares generated outputs with manuscript values
- `expected_results.csv` — manuscript benchmark values
- `test_reproducibility.py` — deterministic and engineering sanity checks
- `reproduce_all.py` — one-command end-to-end reproduction

No folders are required by the source package itself. Generated outputs are written only when scripts are executed.

## Environment

Python 3.11+ is recommended.

```bash
python -m pip install -r requirements.txt
```

## Quick start

Run one deterministic experiment:

```bash
python run_experiments.py --mg 5 --dg FC --scenario base --seed 2026
```

Run 30 repeated stochastic runs:

```bash
python statistical_analysis.py --runs 30 --mg 5 --dg FC --scenario base
```

Run the full study:

```bash
python reproduce_all.py
```

Validate the generated summary against values reported in the manuscript:

```bash
python validate_results.py
```

Run tests:

```bash
python -m unittest test_reproducibility.py
```

## Reproducibility protocol

The default configuration follows the revised manuscript where specified:

- Population size: 50
- Maximum iterations: 200
- Convergence tolerance: 1e-6
- Stagnation window: 10 iterations
- DG capacity: 0.6 MW per unit
- Number of DGs: 3 or 5
- Voltage range: 0.95–1.05 pu
- DG power factor: 0.8–1.0 lagging
- Primary objectives: economic cost, emission cost, voltage deviation
- Secondary reported metrics: active power loss, minimum bus voltage, load-flow evaluations, runtime and unserved load

For computationally lighter local testing, these values can be reduced in `config.yaml`.

## Candidate representation

A candidate solution contains:

1. a reconfiguration vector that selects five open branches from the available sectionalizing and tie-switch set;
2. DG dispatch variables bounded by the configured DG rating;
3. optional reactive support variables;
4. scenario-specific fault constraints.

All candidates are repaired to preserve radial connected topology whenever possible. Infeasible candidates are penalized explicitly.

## Fuzzy aggregation

For a minimization objective `z`, the membership function is:

\[
\mu(z)=
\begin{cases}
1, & z \le z_{\min}\\
\dfrac{z_{\max}-z}{z_{\max}-z_{\min}}, & z_{\min}<z<z_{\max}\\
0, & z \ge z_{\max}
\end{cases}
\]

The compromise fitness is based on the minimum satisfaction across economic cost, emission cost and voltage deviation. Constraint penalties are then added to obtain a minimization score for the search algorithm.

## Constraint handling

The penalty is exposed and reproducible:

\[
\Phi =
\lambda_V \sum_i \Delta V_i^2 +
\lambda_I \sum_\ell \Delta I_\ell^2 +
\lambda_P \Delta P^2 +
\lambda_R \Delta_{\mathrm{radial}} +
\lambda_F \Delta_{\mathrm{fault}} .
\]

All penalty coefficients are editable in `config.yaml`.

## Gradient-based comparison

The original problem is mixed-integer, non-convex and topology-dependent. A gradient-based algorithm therefore cannot solve the exact switching problem without relaxation. `gradient_baseline.py` implements a continuous SLSQP benchmark over DG dispatch for a fixed repaired topology. It is deliberately labelled a relaxation baseline rather than an equivalent solver.

## Convergence and repeated-run analysis

A single convergence curve does not establish reproducibility for a stochastic heuristic. The package therefore supports repeated seeded runs and reports:

- mean
- standard deviation
- median
- interquartile range
- minimum
- maximum
- success rate
- load-flow evaluations
- runtime

## Manuscript consistency checks

`expected_results.csv` contains reported values transcribed from the manuscript, including the base-load tables, algorithm comparison and critical-load/fault summaries. `validate_results.py` does not force agreement; it highlights differences so that manuscript values can be checked against regenerated results.

## Renewable-energy extension

The manuscript states that PV, wind and BESS can be incorporated but does not provide a complete renewable data set or stochastic profile. For scientific transparency, this package does not invent a renewable profile. The generic network/scenario API is written so that such sources can be added after the corresponding data and assumptions are explicitly defined.

## Archiving

After verification, archive the final GitHub release in a DOI-assigning repository such as Zenodo and insert the assigned DOI in the manuscript's Code Availability section. No DOI is fabricated or hard-coded in this package.
