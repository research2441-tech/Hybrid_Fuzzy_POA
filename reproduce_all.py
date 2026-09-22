"""End-to-end reproduction helper."""

import subprocess, sys

def run(cmd):
    print("\n>>>", " ".join(cmd))
    subprocess.run(cmd,check=True)

def main():
    py=sys.executable
    run([py,"run_experiments.py","--mg","5","--dg","FC","--scenario","base","--algorithm","all","--output","results.json"])
    run([py,"generate_figures.py","--results","results.json"])
    run([py,"statistical_analysis.py","--runs","30","--mg","5","--dg","FC","--scenario","base","--output","statistics.csv"])
    run([py,"validate_results.py","--results","results.json"])
    run([py,"-m","unittest","test_reproducibility.py"])
    print("\nReproduction workflow completed.")

if __name__=="__main__":
    main()
