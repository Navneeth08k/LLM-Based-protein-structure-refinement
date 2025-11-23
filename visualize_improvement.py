import numpy as np
import matplotlib.pyplot as plt
from Bio.PDB import PDBParser, Superimposer
from Bio.SeqUtils import seq1
from Bio import Align
import argparse

def get_ca_atoms_and_seq(structure):
    atoms = []
    seq = []
    ids = []
    for r in structure.get_residues():
        if 'CA' in r:
            atoms.append(r['CA'])
            seq.append(seq1(r.get_resname()))
            ids.append(r.id[1])
    return "".join(seq), atoms, ids

def calculate_per_residue_rmsd(ref_atoms, mob_atoms):
    diffs = []
    for r, m in zip(ref_atoms, mob_atoms):
        diff = r - m
        diffs.append(np.linalg.norm(diff))
    return np.array(diffs)

def main():
    parser = argparse.ArgumentParser(description="Visualize per-residue RMSD improvement")
    parser.add_argument("--ground_truth", required=True, help="Path to ground truth PDB")
    parser.add_argument("--original", required=True, help="Path to original PDB")
    parser.add_argument("--refined", required=True, help="Path to refined PDB")
    parser.add_argument("--gt_chain", help="Chain ID for ground truth")
    parser.add_argument("--focus_region", help="Start-End of focus region (1-based)")
    
    args = parser.parse_args()
    
    pdb_parser = PDBParser(QUIET=True)
    
    # Load structures
    gt_struct = pdb_parser.get_structure("gt", args.ground_truth)
    if args.gt_chain:
        gt_model = gt_struct[0][args.gt_chain]
    else:
        gt_model = gt_struct[0]
        
    orig_model = pdb_parser.get_structure("orig", args.original)[0]
    refined_model = pdb_parser.get_structure("refined", args.refined)[0]
    
    # Get sequences and atoms
    gt_seq, gt_atoms, gt_ids = get_ca_atoms_and_seq(gt_model)
    orig_seq, orig_atoms, orig_ids = get_ca_atoms_and_seq(orig_model)
    refined_seq, refined_atoms, refined_ids = get_ca_atoms_and_seq(refined_model)
    
    # Align GT to Original (to map residues)
    aligner = Align.PairwiseAligner()
    aligner.mode = 'global'
    aligner.match_score = 2
    aligner.mismatch_score = -1
    aligner.open_gap_score = -0.5
    aligner.extend_gap_score = -0.1
    
    alignment = aligner.align(gt_seq, orig_seq)[0]
    
    # Collect aligned atoms
    aligned_gt_atoms = []
    aligned_orig_atoms = []
    aligned_refined_atoms = []
    aligned_indices = []
    
    gt_aligned_segments, orig_aligned_segments = alignment.aligned
    
    for (g_start, g_end), (o_start, o_end) in zip(gt_aligned_segments, orig_aligned_segments):
        length = g_end - g_start
        for i in range(length):
            aligned_gt_atoms.append(gt_atoms[g_start + i])
            aligned_orig_atoms.append(orig_atoms[o_start + i])
            aligned_refined_atoms.append(refined_atoms[o_start + i]) # Assuming refined matches original exactly
            aligned_indices.append(orig_ids[o_start + i])

    # Superimpose Original to GT
    sup_orig = Superimposer()
    sup_orig.set_atoms(aligned_gt_atoms, aligned_orig_atoms)
    sup_orig.apply(list(orig_model.get_atoms())) # Apply to full model
    
    # Superimpose Refined to GT
    sup_ref = Superimposer()
    sup_ref.set_atoms(aligned_gt_atoms, aligned_refined_atoms)
    sup_ref.apply(list(refined_model.get_atoms()))
    
    # Calculate per-residue distances (RMSD contribution)
    # Re-fetch coords after superimposition
    # Note: Superimposer modifies atoms in place
    
    dists_orig = []
    dists_refined = []
    
    for gt, orig, ref in zip(aligned_gt_atoms, aligned_orig_atoms, aligned_refined_atoms):
        dists_orig.append(np.linalg.norm(gt.get_coord() - orig.get_coord()))
        dists_refined.append(np.linalg.norm(gt.get_coord() - ref.get_coord()))
        
    dists_orig = np.array(dists_orig)
    dists_refined = np.array(dists_refined)
    
    improvement = dists_orig - dists_refined
    
    # Plot
    plt.figure(figsize=(12, 6))
    plt.bar(aligned_indices, improvement, color='green', label='Improvement (Positive = Closer to GT)')
    plt.axhline(0, color='black', linewidth=0.5)
    plt.xlabel('Residue Index (UniProt)')
    plt.ylabel('RMSD Improvement (Angstroms)')
    plt.title('Per-Residue RMSD Improvement: Refined vs Original')
    plt.legend()
    
    if args.focus_region:
        start, end = map(int, args.focus_region.split('-'))
        plt.axvspan(start, end, color='yellow', alpha=0.2, label='Focus Region')
        
    plt.savefig('rmsd_improvement.png')
    print("Plot saved to rmsd_improvement.png")
    
    # Print stats for focus region
    if args.focus_region:
        start, end = map(int, args.focus_region.split('-'))
        focus_indices = [i for i, idx in enumerate(aligned_indices) if start <= idx <= end]
        if focus_indices:
            focus_imp = improvement[focus_indices]
            print(f"Mean improvement in focus region ({start}-{end}): {np.mean(focus_imp):.4f} A")
            print(f"Max improvement in focus region: {np.max(focus_imp):.4f} A")

if __name__ == "__main__":
    main()
