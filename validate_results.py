"""Compare a generated result with manuscript-reported benchmarks."""

import argparse, csv, json, math
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--results",default="results.json")
    ap.add_argument("--expected",default="expected_results.csv")
    args=ap.parse_args()
    if not Path(args.results).exists():
        print("No generated results.json found. Run run_experiments.py first.")
        return
    data=json.loads(Path(args.results).read_text(encoding="utf-8"))
    expected=list(csv.DictReader(open(args.expected,"r",encoding="utf-8")))

    # Match FuzzyPOA-FC to proposed FC row for convenience.
    exp=[r for r in expected if r["section"]=="Table3" and r["configuration"]=="Proposed_FC"]
    if not exp:
        print("Expected row not found."); return
    e=exp[0]
    generated=next((r for r in data if r.get("algorithm")=="FuzzyPOA"),None)
    if generated is None:
        print("FuzzyPOA result not present."); return
    print("Transparent comparison only; differences are not hidden.")
    for label,gkey,ekey in [
        ("Economic cost","economic_cost","economic_cost"),
        ("Emission cost","emission_cost","emission_cost"),
    ]:
        gv=float(generated[gkey]); ev=float(e[ekey])
        print(f"{label:20s} reported={ev:12.4f} generated={gv:12.4f} difference={gv-ev:12.4f}")

if __name__=="__main__":
    main()
