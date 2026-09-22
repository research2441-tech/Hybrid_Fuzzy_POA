"""Repeated-run analysis for stochastic reproducibility."""

import argparse, csv, statistics, time
from pathlib import Path
import yaml
from scenarios import scenario_from_config
from fuzzy_poa import optimize
from baseline_heuristics import ALGORITHMS

def summary(values):
    v=sorted(float(x) for x in values)
    n=len(v)
    q1=v[max(0,int(0.25*(n-1)))]
    q3=v[min(n-1,int(0.75*(n-1)))]
    return {
        "mean":statistics.fmean(v),
        "std":statistics.stdev(v) if n>1 else 0.0,
        "median":statistics.median(v),
        "iqr":q3-q1,
        "min":min(v),"max":max(v)
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",default="config.yaml")
    ap.add_argument("--runs",type=int,default=None)
    ap.add_argument("--mg",type=int,choices=[3,5],default=5)
    ap.add_argument("--dg",choices=["DE","MT","FC"],default="FC")
    ap.add_argument("--scenario",default="base")
    ap.add_argument("--output",default="statistics.csv")
    args=ap.parse_args()

    cfg=yaml.safe_load(open(args.config,"r",encoding="utf-8"))
    runs=int(args.runs or cfg["repeated_runs"])
    sc=scenario_from_config(cfg,args.scenario)
    methods={"FuzzyPOA":optimize,**ALGORITHMS}
    rows=[]
    for name,fn in methods.items():
        vals=[]; ecc=[]; emc=[]; vdf=[]; runtime=[]; success=[]
        for r in range(runs):
            seed=int(cfg["seed"])+r
            res=fn(args.mg,args.dg,cfg,sc,seed)
            vals.append(res.best.score); ecc.append(res.best.ecc); emc.append(res.best.emc)
            vdf.append(res.best.vdf); runtime.append(res.runtime_s)
            success.append(1 if res.best.penalty==0 else 0)
        s=summary(vals)
        rows.append({
            "algorithm":name,"runs":runs,**{f"score_{k}":v for k,v in s.items()},
            "economic_mean":statistics.fmean(ecc),
            "emission_mean":statistics.fmean(emc),
            "vdf_mean":statistics.fmean(vdf),
            "runtime_mean_s":statistics.fmean(runtime),
            "feasible_success_rate":sum(success)/runs,
        })
    with open(args.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    for row in rows: print(row)

if __name__=="__main__":
    main()
