"""Command-line runner for manuscript experiments."""

import argparse, json
from pathlib import Path
import yaml
from scenarios import scenario_from_config
from fuzzy_poa import optimize
from baseline_heuristics import ALGORITHMS
from gradient_baseline import run_slsqp

def load_cfg(path="config.yaml"):
    with open(path,"r",encoding="utf-8") as f:
        return yaml.safe_load(f)

def serialise_result(name,r):
    b=r.best
    return {
        "algorithm":name,
        "seed":r.seed,
        "score":b.score,
        "fuzzy_membership":b.fuzzy,
        "economic_cost":b.ecc,
        "emission_cost":b.emc,
        "voltage_deviation":b.vdf,
        "loss_kw":b.loss_kw,
        "minimum_voltage_pu":b.vmin,
        "penalty":b.penalty,
        "closed_branches":b.closed,
        "open_branches":sorted(set(range(1,38))-set(b.closed)),
        "dg_dispatch_mw":b.dg_dispatch,
        "load_flow_executions":b.load_flows,
        "runtime_s":r.runtime_s,
        "history":r.history,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",default="config.yaml")
    ap.add_argument("--mg",type=int,choices=[3,5],default=5)
    ap.add_argument("--dg",choices=["DE","MT","FC"],default="FC")
    ap.add_argument("--scenario",default="base")
    ap.add_argument("--seed",type=int,default=None)
    ap.add_argument("--algorithm",choices=["FuzzyPOA","PSO","FFA","MFO","IMFO","SLSQP","all"],default="FuzzyPOA")
    ap.add_argument("--output",default="results.json")
    args=ap.parse_args()
    cfg=load_cfg(args.config)
    seed=cfg["seed"] if args.seed is None else args.seed
    sc=scenario_from_config(cfg,args.scenario)

    out=[]
    if args.algorithm in ("FuzzyPOA","all"):
        out.append(serialise_result("FuzzyPOA",optimize(args.mg,args.dg,cfg,sc,seed)))
    if args.algorithm=="all":
        for name,fn in ALGORITHMS.items():
            out.append(serialise_result(name,fn(args.mg,args.dg,cfg,sc,seed)))
        out.append({"algorithm":"SLSQP","seed":seed,**run_slsqp(args.mg,args.dg,cfg,sc,seed)})
    elif args.algorithm in ALGORITHMS:
        out.append(serialise_result(args.algorithm,ALGORITHMS[args.algorithm](args.mg,args.dg,cfg,sc,seed)))
    elif args.algorithm=="SLSQP":
        out.append({"algorithm":"SLSQP","seed":seed,**run_slsqp(args.mg,args.dg,cfg,sc,seed)})

    Path(args.output).write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps(out,indent=2))

if __name__=="__main__":
    main()
