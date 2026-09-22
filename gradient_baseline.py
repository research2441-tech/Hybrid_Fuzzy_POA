"""Continuous gradient-based relaxation baseline.

The topology is fixed/repaired first because the exact problem contains
discrete switching variables and is not differentiable.
"""

import time
import numpy as np
from scipy.optimize import minimize
from scenarios import dg_buses_for_mg, repair_topology, ALL_BRANCH_IDS
from power_flow import solve_power_flow
from ieee33_data import loads_mw_mvar
from objectives import economic_cost, emission_cost, voltage_deviation
from constraints import penalty

def run_slsqp(mg,dg_type,cfg,scenario,seed=2026):
    rng=np.random.default_rng(seed)
    topo={idx:rng.random() for idx in ALL_BRANCH_IDS}
    closed=repair_topology(topo,scenario["faulted_branches"])
    buses=dg_buses_for_mg(mg)
    cap=float(cfg["dg"]["capacity_mw"])
    p,_=loads_mw_mvar(scenario["load_multiplier"])
    total=float(np.sum(p))
    calls=0

    def fun(x):
        nonlocal calls
        calls+=1
        dispatch={b:float(xx) for b,xx in zip(buses,x)}
        pf=solve_power_flow(closed,scenario["load_multiplier"],dispatch,{},
                            base_kv=float(cfg["network"]["base_kv"]))
        grid=max(0,total+pf.p_loss_mw-sum(dispatch.values()))
        ecc=economic_cost(grid,dispatch,dg_type,cfg)
        emc=emission_cost(grid,dispatch,dg_type,cfg)
        vdf=voltage_deviation(pf.voltage)
        pen=penalty(closed,pf,cfg,scenario["faulted_branches"])
        # normalized continuous objective
        return ecc/250.0 + emc/10000.0 + vdf/2.0 + pen

    x0=np.full(len(buses),0.5*cap)
    t0=time.perf_counter()
    res=minimize(fun,x0,method="SLSQP",bounds=[(0,cap)]*len(buses),
                 options={"maxiter":int(cfg["max_iterations"]),"ftol":1e-9,"disp":False})
    return {
        "success":bool(res.success),
        "message":str(res.message),
        "objective":float(res.fun),
        "dispatch":{b:float(x) for b,x in zip(buses,res.x)},
        "closed_branches":closed,
        "evaluations":calls,
        "runtime_s":time.perf_counter()-t0,
    }
