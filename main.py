import os
import argparse
import numpy as np
from Bio.PDB import PDBParser, PDBIO
from src.analysis.region_finder import RegionFinder
from src.llm.prompt_builder import PromptBuilder
from src.llm.client import OpenAIClient, MockLLMClient, GeminiClient
from src.llm.context_agent import ContextAgent
from src.geometry.refiner import GeometricRefiner
from src.physics.minimizer import EnergyMinimizer
from src.utils.data_fetcher import AlphaFoldFetcher
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="LLM-Guided Protein Refinement")
    parser.add_argument("--uniprot", type=str, help="Uniprot ID to fetch (e.g., Q92947)")
    parser.add_argument("--json", type=str, help="Path to confidence JSON file")
    parser.add_argument("--output", type=str, default="refined_structure.pdb", help="Output PDB path")
    parser.add_argument("--provider", type=str, default="gemini", choices=["openai", "gemini", "mock"], help="LLM provider")
    parser.add_argument("--api_key", type=str, help="API Key for the provider")
    parser.add_argument("--ground_truth", type=str, help="PDB ID or path to experimental structure for comparison")
    parser.add_argument("--gt_chain", type=str, help="Chain ID of the ground truth structure to compare against")
    parser.add_argument("--context", type=str, help="Biological context for the protein")
    parser.add_argument("--auto_context", action="store_true", help="Automatically retrieve biological context using LLM")
    parser.add_argument("--focus_region", type=str, help="Specific region to refine (start-end, 1-based), overriding automatic detection")
    
    args = parser.parse_args()

    # Initialize LLM Client early
    if args.provider == "mock":
        llm_client = MockLLMClient()
    elif args.provider == "openai":
        llm_client = OpenAIClient(api_key=args.api_key)
    elif args.provider == "gemini":
        llm_client = GeminiClient(api_key=args.api_key)

    # 0. Fetch Data if Uniprot ID provided
    if args.uniprot:
        print(f"Fetching data for Uniprot ID: {args.uniprot}")
        fetcher = AlphaFoldFetcher()
        pdb_path, json_path = fetcher.fetch(args.uniprot)
    else:
        pdb_path = args.pdb
        json_path = args.json
        
    if not pdb_path or not json_path:
        print("Error: Must provide either --uniprot or both --pdb and --json")
        return

    # Determine Context
    context = args.context
    if args.auto_context and not context:
        if args.uniprot:
            print("Auto-detecting biological context...")
            context_agent = ContextAgent(llm_client)
            context = context_agent.get_context(args.uniprot)
            with open("pipeline_debug.log", "a") as log:
                log.write(f"--- AutoContext for {args.uniprot} ---\n")
                log.write(f"Retrieved Context: {context}\n")
        else:
            print("Warning: --auto_context requires --uniprot ID. Skipping auto-context.")

    # 1. Identify Regions
    print(f"Identifying low-confidence regions in {pdb_path}...")
    finder = RegionFinder(plddt_threshold=70.0)
    
    # Load scores
    try:
        plddt_scores = finder.load_confidence_json(json_path)
    except Exception as e:
        print(f"Error loading confidence JSON: {e}")
        return

    if args.focus_region:
        try:
            start, end = map(int, args.focus_region.split('-'))
            # Convert 1-based inclusive (user) to 0-based exclusive (Python slice)
            # User input: 786-826 -> 0-based start 785, 0-based end 826
            regions = [(start - 1, end)]
            print(f"Focusing on user-specified region: {start}-{end} (Internal: {start-1}-{end})")
        except ValueError:
            print("Invalid format for --focus_region. Use start-end (e.g., 786-826).")
            return
    else:
        regions = finder.find_regions_from_scores(plddt_scores)
    
    if not regions:
        print("No low-confidence regions found. Skipping refinement.")
        return

    print(f"Found {len(regions)} regions to refine.")

    # Load PDB
    pdb_parser = PDBParser()
    structure = pdb_parser.get_structure("protein", pdb_path)
    # Assuming single chain for simplicity
    chain = list(structure.get_chains())[0]
    residues = list(chain.get_residues())
    
    # Extract sequence
    # BioPython residues to sequence... simplified
    from Bio.SeqUtils import seq1
    sequence = "".join([seq1(r.get_resname()) for r in residues])

    # 2. LLM Query & 3. Geometric Refinement
    prompt_builder = PromptBuilder()
    
    # Client already initialized
    
    refiner = GeometricRefiner()
    
    # Get all CA coordinates for simple refinement
    # In a real scenario, we'd handle full atom
    ca_atoms = [r['CA'] for r in residues if 'CA' in r]
    coords = np.array([a.get_coord() for a in ca_atoms])
    
    for start, end in regions:
        # Extract region details
        region_seq = sequence[start:end]
        region_plddt = plddt_scores[start:end]
        
        print(f"Refining region {start}-{end} ({region_seq})...")
        
        # Build Prompt
        prompt = prompt_builder.build_prompt(region_seq, region_plddt, context=args.context)
        
        # Query LLM
        print("Querying LLM...")
        response = llm_client.query(prompt)
        
        with open("pipeline_debug.log", "a") as log:
            log.write(f"--- Region {start}-{end} ---\n")
            log.write(f"Prompt: {prompt[:100]}...\n")
            log.write(f"Response: {response}\n")
            
        if not response:
            print("LLM query failed. Skipping.")
            continue
            
        print(f"LLM Suggestion: {response.get('secondary_structure_prediction')}")
        
        # Parse constraints
        constraints = []
        llm_constraints = response.get('constraints', [])
        
        for c in llm_constraints:
            try:
                # LLM returns 1-based indices relative to the snippet
                # We need to convert to 0-based indices relative to the FULL sequence
                # snippet index i (1-based) -> snippet index i-1 (0-based) -> full index start + i - 1
                
                r1_local = c.get('residue_index_1')
                r2_local = c.get('residue_index_2')
                dist = c.get('distance_angstroms', 5.0)
                ctype = c.get('type', 'distance')
                
                if r1_local is not None and r2_local is not None:
                    idx1 = start + r1_local - 1
                    idx2 = start + r2_local - 1
                    
                    # Basic validation
                    if 0 <= idx1 < len(coords) and 0 <= idx2 < len(coords):
                        constraints.append({
                            'type': ctype,
                            'indices': [idx1, idx2],
                            'value': float(dist)
                        })
                        print(f"  Added constraint: {idx1}-{idx2} dist={dist}")
                        with open("pipeline_debug.log", "a") as log:
                            log.write(f"  Applied constraint: {idx1}-{idx2} dist={dist}\n")
            except Exception as e:
                print(f"  Failed to parse constraint {c}: {e}")

        # If using mock LLM and no constraints returned (or just to ensure we have something to test)
        if args.provider == "mock" and not constraints:
             # Create a dummy distance constraint between start and start+3
            if end - start > 3:
                constraints.append({
                    'type': 'distance',
                    'indices': [start, start+3],
                    'value': 5.0 # Angstroms
                })
        
        # Refine
        # We pass the FULL coordinates but only mask the region?
        # Or we just refine the region?
        # Refiner expects full coords and a mask
        mask = np.zeros(len(coords), dtype=bool)
        mask[start:end] = True
        
        refined_coords = refiner.refine(coords, constraints, mask=mask)
        coords = refined_coords # Update for next iteration

    # Update Structure with refined coordinates
    for i, atom in enumerate(ca_atoms):
        atom.set_coord(coords[i])

    # Save intermediate
    io = PDBIO()
    io.set_structure(structure)
    intermediate_pdb = "intermediate_refined.pdb"
    io.save(intermediate_pdb)

    # 5. Physics Minimization (Optional/Fallback)
    print("Running physics minimization...")
    minimizer = EnergyMinimizer()
    minimizer.minimize(intermediate_pdb, args.output)
    
    # 6. Evaluation (Optional)
    if args.ground_truth:
        from src.analysis.evaluator import Evaluator
        from src.utils.data_fetcher import RCSBFetcher
        
        print("\n--- Evaluation ---")
        evaluator = Evaluator()
        
        # Check if ground_truth is a file path or a PDB ID
        if os.path.exists(args.ground_truth):
            gt_path = args.ground_truth
        else:
            # Assume it's a PDB ID and fetch it
            rcsb = RCSBFetcher()
            gt_path = rcsb.fetch(args.ground_truth)
            
        if gt_path:
            results = evaluator.compare(gt_path, pdb_path, args.output, gt_chain=args.gt_chain)
            print(f"RMSD (Original vs Ground Truth): {results['rmsd_original']:.3f} A")
            print(f"RMSD (Refined vs Ground Truth):  {results['rmsd_refined']:.3f} A")
            print(f"Improvement:                     {results['improvement']:.3f} A")
            
            if results['improvement'] > 0:
                print("SUCCESS: Refined model is closer to experimental structure!")
            else:
                print("Note: Refined model drifted further (or ground truth covers different domain).")
                
            with open("evaluation_results.txt", "w") as f:
                f.write(f"RMSD_Original: {results['rmsd_original']:.3f}\n")
                f.write(f"RMSD_Refined: {results['rmsd_refined']:.3f}\n")
                f.write(f"Improvement: {results['improvement']:.3f}\n")
    
    print("Done!")

if __name__ == "__main__":
    main()
