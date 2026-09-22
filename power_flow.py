"""Radial backward/forward-sweep distribution load flow."""

from dataclasses import dataclass
import numpy as np
from ieee33_data import N_BUSES, SLACK_BUS, branch_dict, loads_mw_mvar

@dataclass
class PowerFlowResult:
    converged: bool
    voltage: np.ndarray
    branch_current: dict
    p_loss_mw: float
    q_loss_mvar: float
    iterations: int
    disconnected_buses: list

def _adjacency(closed):
    bd = branch_dict()
    adj = {i: [] for i in range(1, N_BUSES + 1)}
    for idx in closed:
        b = bd[idx]
        adj[b.fbus].append((b.tbus, idx))
        adj[b.tbus].append((b.fbus, idx))
    return adj

def radial_order(closed):
    adj = _adjacency(closed)
    parent = {SLACK_BUS: None}
    parent_branch = {}
    order = [SLACK_BUS]
    for u in order:
        for v, idx in adj[u]:
            if v not in parent:
                parent[v] = u
                parent_branch[v] = idx
                order.append(v)
    disconnected = [b for b in range(1, N_BUSES + 1) if b not in parent]
    return order, parent, parent_branch, disconnected

def solve_power_flow(closed_branches, load_multiplier=1.0, dg_p=None, dg_q=None,
                     base_kv=12.66, max_iter=100, tol=1e-8):
    """Solve a connected radial topology.

    Parameters
    ----------
    closed_branches : iterable of branch indices
    dg_p, dg_q : dictionaries {bus: MW/MVAr}
    """
    closed = sorted(set(int(x) for x in closed_branches))
    order, parent, parent_branch, disconnected = radial_order(closed)
    v = np.ones(N_BUSES + 1, dtype=complex)
    if disconnected:
        return PowerFlowResult(False, v, {}, 1e6, 1e6, 0, disconnected)

    p, q = loads_mw_mvar(load_multiplier)
    dg_p = dg_p or {}
    dg_q = dg_q or {}
    for bus, val in dg_p.items():
        p[int(bus)] -= float(val)
    for bus, val in dg_q.items():
        q[int(bus)] -= float(val)

    bd = branch_dict()
    zbase = (base_kv ** 2) / 10.0  # base MVA = 10
    zpu = {idx: complex(bd[idx].r_ohm, bd[idx].x_ohm)/zbase for idx in closed}
    sbase = 10.0
    s = (p + 1j*q)/sbase

    branch_i = {}
    for it in range(max_iter):
        vold = v.copy()
        iinj = np.zeros(N_BUSES + 1, dtype=complex)
        for bus in range(2, N_BUSES + 1):
            if abs(v[bus]) < 1e-12:
                v[bus] = 1+0j
            iinj[bus] = np.conj(s[bus] / v[bus])

        downstream = iinj.copy()
        for bus in reversed(order[1:]):
            idx = parent_branch[bus]
            branch_i[idx] = downstream[bus]
            downstream[parent[bus]] += downstream[bus]

        v[SLACK_BUS] = 1+0j
        for bus in order[1:]:
            idx = parent_branch[bus]
            v[bus] = v[parent[bus]] - zpu[idx]*branch_i[idx]

        if np.max(np.abs(v - vold)) < tol:
            break

    p_loss = 0.0
    q_loss = 0.0
    for idx, cur in branch_i.items():
        z = zpu[idx]
        sloss_pu = (abs(cur)**2) * z
        p_loss += sloss_pu.real * sbase
        q_loss += sloss_pu.imag * sbase

    return PowerFlowResult(True, v, branch_i, p_loss, q_loss, it+1, [])
