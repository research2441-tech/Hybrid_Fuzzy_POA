"""Hybrid Fuzzy-Puzzle Optimization Algorithm.

The manuscript describes a two-stage POA update and fuzzy compromise. This
implementation keeps those two stages explicit, uses seeded stochastic search,
topology repair, penalties, and convergence-history logging.
"""

from dataclasses import dataclass
import time
import numpy as np
from ieee33_data import N_BUSES, loads_mw_mvar
from scenarios import repair_topology, dg_buses_for_mg, ALL_BRANCH_IDS
from power_flow import solve_power_flow
from constraints import penalty
from objectives import economic_cost, emission_cost, voltage_deviation, minimum_voltage, compromise_membership

@dataclass
class Evaluation:
    score: float
    fuzzy: float
    ecc: float
    emc: float
    vdf: float
    loss_kw: float
    vmin: float
    closed: list
    dg_dispatch: dict
    penalty: float
    load_flows: int

@dataclass
class OptimizationResult:
    best: Evaluation
    best_vector: np.ndarray
    history: list
    runtime_s: float
    seed: int

def _reference_objectives(cfg, scenario, dg_type, mg):
    # Build physically interpretable fuzzy anchors from no-DG initial system.
    p, _ = loads_mw_mvar(scenario["load_multiplier"])
    total_load = float(np.sum(p))
    # broad anchors avoid hard-coding the manuscript's final result
    grid_cost = total_load * cfg["grid"]["variable_cost_per_mwh"]
    grid_em = total_load * cfg["grid"]["emission_lb_per_mwh"]
    return {
        "ecc_good": 0.50*grid_cost,
        "ecc_bad": 1.05*grid_cost,
        "emc_good": 0.50*grid_em,
        "emc_bad": 1.05*grid_em,
        "vdf_good": 0.05,
        "vdf_bad": max(0.10, 0.03*N_BUSES),
    }

def _decode(x, mg, cfg, scenario):
    nb = len(ALL_BRANCH_IDS)
    topo = {idx: float(x[k]) for k, idx in enumerate(ALL_BRANCH_IDS)}
    closed = repair_topology(topo, scenario["faulted_branches"])
    buses = dg_buses_for_mg(mg)
    cap = float(cfg["dg"]["capacity_mw"])
    dispatch = {bus: cap*float(np.clip(x[nb+i], 0, 1)) for i,bus in enumerate(buses)}
    return closed, dispatch

def evaluate_vector(x, mg, dg_type, cfg, scenario, reference=None):
    reference = reference or _reference_objectives(cfg, scenario, dg_type, mg)
    closed, dispatch = _decode(x, mg, cfg, scenario)
    pf = solve_power_flow(
        closed,
        load_multiplier=scenario["load_multiplier"],
        dg_p=dispatch,
        dg_q={},
        base_kv=float(cfg["network"]["base_kv"])
    )
    p, _ = loads_mw_mvar(scenario["load_multiplier"])
    total_load = float(np.sum(p))
    dg_total = float(sum(dispatch.values()))
    grid_mw = max(0.0, total_load + pf.p_loss_mw - dg_total)

    ecc = economic_cost(grid_mw, dispatch, dg_type, cfg)
    emc = emission_cost(grid_mw, dispatch, dg_type, cfg)
    vdf = voltage_deviation(pf.voltage)
    fuzzy, _ = compromise_membership(ecc, emc, vdf, reference)
    pen = penalty(closed, pf, cfg, scenario["faulted_branches"])

    # Search minimizes score. Fuzzy satisfaction is therefore converted to 1-mu.
    score = (1.0 - fuzzy) + pen
    return Evaluation(
        score=float(score),
        fuzzy=float(fuzzy),
        ecc=float(ecc),
        emc=float(emc),
        vdf=float(vdf),
        loss_kw=float(pf.p_loss_mw*1000.0),
        vmin=minimum_voltage(pf.voltage),
        closed=closed,
        dg_dispatch=dispatch,
        penalty=float(pen),
        load_flows=1,
    )

def optimize(mg, dg_type, cfg, scenario, seed=None):
    seed = int(cfg.get("seed",2026) if seed is None else seed)
    rng = np.random.default_rng(seed)
    n = int(cfg["population_size"])
    tmax = int(cfg["max_iterations"])
    tol = float(cfg["convergence_tolerance"])
    window = int(cfg["stagnation_window"])
    dim = len(ALL_BRANCH_IDS) + int(mg)

    pop = rng.random((n, dim))
    reference = _reference_objectives(cfg, scenario, dg_type, mg)

    t0=time.perf_counter()
    evals=[evaluate_vector(v,mg,dg_type,cfg,scenario,reference) for v in pop]
    lf=n
    scores=np.array([e.score for e in evals])
    best_i=int(np.argmin(scores))
    best_vec=pop[best_i].copy()
    best=evals[best_i]
    history=[best.score]
    stale=0

    for it in range(tmax):
        old_best=best.score

        # Stage 1: advice from another population member and current best.
        for i in range(n):
            j=int(rng.integers(0,n-1))
            if j>=i: j+=1
            r1=rng.random(dim)
            r2=rng.random(dim)
            candidate = pop[i] + r1*(pop[j]-pop[i]) + r2*(best_vec-pop[i])
            candidate=np.clip(candidate,0,1)
            ev=evaluate_vector(candidate,mg,dg_type,cfg,scenario,reference); lf+=1
            if ev.score < evals[i].score:
                pop[i]=candidate; evals[i]=ev

        # Stage 2: puzzle-piece mixing + local adaptive perturbation.
        order=rng.permutation(n)
        scale=max(0.02, 0.25*(1.0-it/max(1,tmax)))
        for k,i in enumerate(order):
            donor=order[(k+1)%n]
            mask=rng.random(dim)<0.5
            candidate=np.where(mask,pop[donor],pop[i])
            candidate += rng.normal(0.0, scale, size=dim)*(best_vec-candidate)
            candidate=np.clip(candidate,0,1)
            ev=evaluate_vector(candidate,mg,dg_type,cfg,scenario,reference); lf+=1
            if ev.score < evals[i].score:
                pop[i]=candidate; evals[i]=ev

        scores=np.array([e.score for e in evals])
        bi=int(np.argmin(scores))
        if scores[bi] < best.score:
            best_vec=pop[bi].copy()
            best=evals[bi]
        history.append(best.score)

        improvement=abs(old_best-best.score)
        stale = stale+1 if improvement < tol else 0
        if stale >= window:
            break

    runtime=time.perf_counter()-t0
    best.load_flows=lf
    return OptimizationResult(best,best_vec,history,runtime,seed)
