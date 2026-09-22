"""Operating-scenario definitions and topology repair."""

import numpy as np
from ieee33_data import NORMALLY_OPEN, NORMALLY_CLOSED, branch_dict, N_BUSES
from constraints import graph_properties

ALL_BRANCH_IDS = sorted(branch_dict().keys())

def scenario_from_config(cfg, name):
    if name not in cfg["scenarios"]:
        raise KeyError(f"Unknown scenario: {name}")
    d = cfg["scenarios"][name]
    return {
        "name": name,
        "load_multiplier": float(d.get("load_multiplier", 1.0)),
        "faulted_branches": [int(x) for x in d.get("faulted_branches", [])]
    }

def initial_closed(faulted=()):
    return [x for x in NORMALLY_CLOSED if x not in set(faulted)]

def repair_topology(open_scores, faulted=()):
    """Create a connected radial topology by Kruskal-like edge selection.

    Lower open_score => edge is preferred to remain closed.
    Faulted branches are forced open.
    """
    bd = branch_dict()
    faulted = set(int(x) for x in faulted)

    parent = list(range(N_BUSES+1))
    def find(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]]
            a=parent[a]
        return a
    def union(a,b):
        ra, rb = find(a), find(b)
        if ra==rb: return False
        parent[rb]=ra
        return True

    ranked = []
    for idx in ALL_BRANCH_IDS:
        if idx in faulted:
            continue
        score = float(open_scores.get(idx, 0.5))
        # Normally closed branches get a mild preference.
        bias = 0.0 if idx in NORMALLY_CLOSED else 0.05
        ranked.append((score+bias, idx))
    ranked.sort()

    closed=[]
    for _, idx in ranked:
        b=bd[idx]
        if union(b.fbus,b.tbus):
            closed.append(idx)
        if len(closed)==N_BUSES-1:
            break
    return sorted(closed)

def dg_buses_for_mg(mg):
    from ieee33_data import DG_BUSES_3MG, DG_BUSES_5MG
    if int(mg)==3:
        return list(DG_BUSES_3MG)
    if int(mg)==5:
        return list(DG_BUSES_5MG)
    raise ValueError("mg must be 3 or 5")
