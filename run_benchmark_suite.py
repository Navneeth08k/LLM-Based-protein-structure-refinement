import csv
import subprocess
import pandas as pd
import os
import time

import argparse
from dotenv import load_dotenv

load_dotenv()

def run_benchmark(row, use_auto_context=False):
    uniprot_id = row['uniprot_id']
    gt_pdb = row['ground_truth_pdb']
    gt_chain = row['gt_chain']
    focus_region = row['focus_region']
    context = row['context']
    
    print(f"--- Running Benchmark for {uniprot_id} (GT: {gt_pdb}) ---")
    
    cmd = [
        r".\venv\Scripts\python", "main.py",
        "--uniprot", uniprot_id,
        "--provider", "gemini",
        "--api_key", os.getenv("GEMINI_API_KEY", ""), # Securely fetch from env
        "--ground_truth", gt_pdb,
        "--ground_truth", gt_pdb,
        "--gt_chain", gt_chain,
    ]

    if pd.notna(focus_region) and str(focus_region).strip():
        cmd.extend(["--focus_region", str(focus_region)])

    if use_auto_context:
        cmd.append("--auto_context")
    else:
        cmd.extend(["--context", context])
    
    # Clean up previous results
    if os.path.exists("evaluation_results.txt"):
        os.remove("evaluation_results.txt")

    try:
        # Run the pipeline
        subprocess.run(cmd, check=True)
        
        # Read the result
        if os.path.exists("evaluation_results.txt"):
            with open("evaluation_results.txt", "r") as f:
                lines = f.readlines()
                # Parse RMSD values
                rmsd_orig = float(lines[0].split(":")[1].strip())
                rmsd_refined = float(lines[1].split(":")[1].strip())
                improvement = float(lines[2].split(":")[1].strip())
                return rmsd_orig, rmsd_refined, improvement
        else:
            print(f"Error: evaluation_results.txt not generated for {uniprot_id}.")
            return None, None, None
            
    except subprocess.CalledProcessError as e:
        print(f"Error running pipeline for {uniprot_id}: {e}")
        return None, None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None, None

def main():
    parser = argparse.ArgumentParser(description="Run Benchmark Suite")
    parser.add_argument("--auto_context", action="store_true", help="Use automated context retrieval instead of CSV context")
    args = parser.parse_args()

    benchmarks = pd.read_csv("benchmarks.csv")
    results = []
    
    for _, row in benchmarks.iterrows():
        rmsd_orig, rmsd_refined, improvement = run_benchmark(row, use_auto_context=args.auto_context)
        
        result_entry = {
            "uniprot_id": row['uniprot_id'],
            "target": row['ground_truth_pdb'],
            "rmsd_original": rmsd_orig,
            "rmsd_refined": rmsd_refined,
            "improvement": improvement,
            "status": "Success" if improvement is not None else "Failed"
        }
        results.append(result_entry)
        print(f"Result: {result_entry}\n")
        time.sleep(2) # Brief pause
        
    # Save results
    df = pd.DataFrame(results)
    df.to_csv("benchmark_results.csv", index=False)
    print("\n--- Benchmark Suite Completed ---")
    print(df)

if __name__ == "__main__":
    main()
