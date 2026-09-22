"""Engineering feasibility and explicit penalty handling."""

from collections import deque
import numpy as np
from ieee33_data import N_BUSES, SLACK_BUS, branch_dict

def graph_properties(closed):
    bd = branch_dict()
    adj = {i: [] for i in range(1, N_BUSES+1)}
    edge_count = 0
    for idx in set(closed):
        b = bd[idx]
        adj[b.fbus].append(b.tbus)
        adj[b.tbus].append(b.fbus)
        edge_count += 1
    seen = {SLACK_BUS}
    q = deque([SLACK_BUS])
    while q:
        u=q.popleft()
        for v in adj[u]:
            if v not in seen:
                seen.add(v); q.append(v)
    connected = len(seen)==N_BUSES
    radial = connected and edge_count==N_BUSES-1
    return connected, radial

def penalty(closed, pf, cfg, faulted_branches=()):
    pcfg = cfg["penalty"]
    value = 0.0
    connected, radial = graph_properties(closed)
    if not connected:
        value += float(pcfg["disconnected"]) * max(1, len(pf.disconnected_buses))
    if not radial:
        value += float(pcfg["cycle"])

    vmag = np.abs(pf.voltage[1:])
    vlo = cfg["network"]["voltage_min_pu"]
    vhi = cfg["network"]["voltage_max_pu"]
    underv = np.maximum(vlo-vmag, 0.0)
    overv = np.maximum(vmag-vhi, 0.0)
    value += float(pcfg["voltage"]) * float(np.sum(underv**2 + overv**2))

    ilimit = cfg["network"]["line_current_limit_pu"]
    if pf.branch_current:
        amps = np.array([abs(x) for x in pf.branch_current.values()])
        value += float(pcfg["current"]) * float(np.sum(np.maximum(amps-ilimit,0.0)**2))

    closed_set = set(closed)
    for f in faulted_branches:
        if int(f) in closed_set:
            value += float(pcfg["fault"])
    return float(value)
