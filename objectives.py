"""Objective functions for the Hybrid Fuzzy-POA study."""

import numpy as np

def economic_cost(grid_mw, dg_dispatch, dg_type, cfg):
    # $/h, using explicit editable coefficients from config.yaml
    gc = cfg["grid"]["variable_cost_per_mwh"] * max(grid_mw, 0.0)
    dc = cfg["dg"]["types"][dg_type]["variable_cost_per_mwh"] * sum(max(x,0.0) for x in dg_dispatch.values())
    return gc + dc

def emission_cost(grid_mw, dg_dispatch, dg_type, cfg):
    # lb/h
    ge = cfg["grid"]["emission_lb_per_mwh"] * max(grid_mw, 0.0)
    de = cfg["dg"]["types"][dg_type]["emission_lb_per_mwh"] * sum(max(x,0.0) for x in dg_dispatch.values())
    return ge + de

def voltage_deviation(voltage):
    mag = np.abs(voltage[1:])
    return float(np.sum(np.abs(1.0 - mag)))

def minimum_voltage(voltage):
    return float(np.min(np.abs(voltage[1:])))

def fuzzy_min_membership(value, good, bad):
    """Membership 1 at/below good, 0 at/above bad for a minimized objective."""
    if bad <= good:
        raise ValueError("bad must be greater than good")
    if value <= good:
        return 1.0
    if value >= bad:
        return 0.0
    return float((bad - value)/(bad - good))

def compromise_membership(ecc, emc, vdf, reference):
    """Min-satisfaction fuzzy compromise."""
    me = fuzzy_min_membership(ecc, reference["ecc_good"], reference["ecc_bad"])
    mm = fuzzy_min_membership(emc, reference["emc_good"], reference["emc_bad"])
    mv = fuzzy_min_membership(vdf, reference["vdf_good"], reference["vdf_bad"])
    return min(me, mm, mv), {"economic": me, "emission": mm, "voltage": mv}
