"""Baseline stochastic optimizers using the identical evaluation function."""

from dataclasses import dataclass
import time
import numpy as np
from scenarios import ALL_BRANCH_IDS
from fuzzy_poa import evaluate_vector, _reference_objectives, OptimizationResult

def _setup(mg,cfg,seed):
    rng=np.random.default_rng(seed)
    n=int(cfg["population_size"]); tmax=int(cfg["max_iterations"])
    dim=len(ALL_BRANCH_IDS)+int(mg)
    return rng,n,tmax,dim

def pso(mg,dg_type,cfg,scenario,seed=2026):
    rng,n,tmax,dim=_setup(mg,cfg,seed)
    ref=_reference_objectives(cfg,scenario,dg_type,mg)
    x=rng.random((n,dim)); v=rng.normal(0,0.05,(n,dim))
    ev=[evaluate_vector(z,mg,dg_type,cfg,scenario,ref) for z in x]; lf=n
    pbest=x.copy(); pev=ev[:]
    gi=int(np.argmin([e.score for e in ev])); g=x[gi].copy(); gev=ev[gi]
    hist=[gev.score]; t0=time.perf_counter()
    for t in range(tmax):
        w=0.9-0.5*t/max(1,tmax-1)
        r1=rng.random((n,dim)); r2=rng.random((n,dim))
        v=w*v+1.7*r1*(pbest-x)+1.7*r2*(g-x)
        x=np.clip(x+v,0,1)
        for i in range(n):
            e=evaluate_vector(x[i],mg,dg_type,cfg,scenario,ref); lf+=1
            if e.score<pev[i].score:
                pbest[i]=x[i].copy(); pev[i]=e
                if e.score<gev.score:
                    g=x[i].copy(); gev=e
        hist.append(gev.score)
    gev.load_flows=lf
    return OptimizationResult(gev,g,hist,time.perf_counter()-t0,seed)

def fpa(mg,dg_type,cfg,scenario,seed=2026):
    """Flower-pollination/FFA-style comparison baseline."""
    rng,n,tmax,dim=_setup(mg,cfg,seed)
    ref=_reference_objectives(cfg,scenario,dg_type,mg)
    x=rng.random((n,dim))
    ev=[evaluate_vector(z,mg,dg_type,cfg,scenario,ref) for z in x]; lf=n
    gi=int(np.argmin([e.score for e in ev])); g=x[gi].copy(); gev=ev[gi]
    hist=[gev.score]; t0=time.perf_counter()
    for _ in range(tmax):
        for i in range(n):
            if rng.random()<0.8:
                step=rng.normal(0,0.08,dim)*(g-x[i])
                cand=x[i]+step
            else:
                j,k=rng.choice(n,2,replace=False)
                cand=x[i]+rng.random(dim)*(x[j]-x[k])
            cand=np.clip(cand,0,1)
            e=evaluate_vector(cand,mg,dg_type,cfg,scenario,ref); lf+=1
            if e.score<ev[i].score:
                x[i]=cand; ev[i]=e
                if e.score<gev.score: g=cand.copy(); gev=e
        hist.append(gev.score)
    gev.load_flows=lf
    return OptimizationResult(gev,g,hist,time.perf_counter()-t0,seed)

def mfo(mg,dg_type,cfg,scenario,seed=2026,improved=False):
    rng,n,tmax,dim=_setup(mg,cfg,seed)
    ref=_reference_objectives(cfg,scenario,dg_type,mg)
    x=rng.random((n,dim))
    ev=[evaluate_vector(z,mg,dg_type,cfg,scenario,ref) for z in x]; lf=n
    hist=[]; t0=time.perf_counter()
    for t in range(tmax):
        order=np.argsort([e.score for e in ev])
        flames=x[order].copy()
        best_ev=ev[order[0]]
        hist.append(best_ev.score)
        flame_count=max(1,int(round(n-(n-1)*t/max(1,tmax-1))))
        for i in range(n):
            f=flames[min(i,flame_count-1)]
            b=1.0
            spiral=(2*rng.random(dim)-1)
            dist=np.abs(f-x[i])
            cand=dist*np.exp(b*spiral)*np.cos(2*np.pi*spiral)+f
            if improved:
                cand=0.85*cand+0.15*flames[0]+rng.normal(0,0.01,dim)
            cand=np.clip(cand,0,1)
            e=evaluate_vector(cand,mg,dg_type,cfg,scenario,ref); lf+=1
            if e.score<ev[i].score:
                x[i]=cand; ev[i]=e
    order=np.argsort([e.score for e in ev])
    bi=order[0]; ev[bi].load_flows=lf
    return OptimizationResult(ev[bi],x[bi].copy(),hist,time.perf_counter()-t0,seed)

def imfo(mg,dg_type,cfg,scenario,seed=2026):
    return mfo(mg,dg_type,cfg,scenario,seed,improved=True)

ALGORITHMS={"PSO":pso,"FFA":fpa,"MFO":mfo,"IMFO":imfo}
