"""Publication-quality figure generation from result JSON files."""

import argparse, json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import yaml

def convergence_plot(result_json, out="convergence_comparison.png"):
    data=json.loads(Path(result_json).read_text(encoding="utf-8"))
    fig,ax=plt.subplots(figsize=(7.2,4.8))
    for r in data:
        if "history" not in r: continue
        y=np.asarray(r["history"],float)
        ax.plot(np.arange(len(y)),y,label=r["algorithm"],linewidth=1.8)
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Best penalized objective")
    ax.grid(True,alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out,dpi=600,bbox_inches="tight")
    fig.savefig(Path(out).with_suffix(".pdf"),bbox_inches="tight")
    plt.close(fig)

def metric_bar(result_json, key, ylabel, out):
    data=json.loads(Path(result_json).read_text(encoding="utf-8"))
    names=[]; vals=[]
    for r in data:
        if key in r:
            names.append(r["algorithm"]); vals.append(r[key])
    fig,ax=plt.subplots(figsize=(7.2,4.8))
    ax.bar(names,vals)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x",rotation=25)
    ax.grid(True,axis="y",alpha=0.25)
    fig.tight_layout()
    fig.savefig(out,dpi=600,bbox_inches="tight")
    plt.close(fig)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--results",default="results.json")
    args=ap.parse_args()
    convergence_plot(args.results)
    metric_bar(args.results,"economic_cost","Economic cost ($/h)","economic_cost_comparison.png")
    metric_bar(args.results,"emission_cost","Emission cost (lb/h)","emission_cost_comparison.png")
    print("Generated convergence_comparison.png/.pdf and comparison figures.")

if __name__=="__main__":
    main()
