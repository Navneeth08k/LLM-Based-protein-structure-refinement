import numpy as np
from Bio.PDB import Superimposer, PDBParser

class Evaluator:
    """
    Evaluates structural quality and accuracy.
    """
    def __init__(self):
        self.parser = PDBParser(QUIET=True)

    def load_structure(self, pdb_path, model_id=0, chain_id=None):
        structure = self.parser.get_structure("struct", pdb_path)
        model = structure[model_id]
        if chain_id:
            if chain_id in model:
                return model[chain_id]
            else:
                print(f"Warning: Chain {chain_id} not found in {pdb_path}. Using first chain.")
                return list(model.get_chains())[0]
        return model

    def calculate_rmsd(self, ref_structure, mobile_structure, atoms_to_use=None):
        """
        Aligns mobile_structure to ref_structure and calculates RMSD.
        Uses sequence alignment to map residues between structures.
        """
        from Bio import Align
        from Bio.SeqUtils import seq1

        # Helper to get sequence and residues
        def get_seq_and_res(structure):
            residues = [r for r in structure.get_residues() if 'CA' in r]
            seq = "".join([seq1(r.get_resname()) for r in residues])
            return seq, residues

        ref_seq, ref_residues = get_seq_and_res(ref_structure)
        mob_seq, mob_residues = get_seq_and_res(mobile_structure)

        # Align sequences
        aligner = Align.PairwiseAligner()
        aligner.mode = 'global'
        aligner.match_score = 2
        aligner.mismatch_score = -1
        aligner.open_gap_score = -0.5
        aligner.extend_gap_score = -0.1
        
        alignments = aligner.align(ref_seq, mob_seq)
        alignment = alignments[0] # Take best alignment
        
        # Map residues based on alignment
        ref_atoms = []
        mobile_atoms = []
        
        # Iterate through alignment indices
        # alignment.indices is (indices1, indices2)
        # But simpler to walk the alignment
        
        # alignment.aligned is tuple of two lists of (start, end) tuples
        ref_aligned_segments, mob_aligned_segments = alignment.aligned
        
        # We need to iterate and collect atoms
        # This is slightly complex with segments, let's iterate character by character?
        # No, segments are easier.
        
        for (r_start, r_end), (m_start, m_end) in zip(ref_aligned_segments, mob_aligned_segments):
            # Lengths should be equal for aligned segments
            length = r_end - r_start
            if (m_end - m_start) != length:
                 print("Error: Aligned segment lengths mismatch.")
                 continue
                 
            for i in range(length):
                r_idx = r_start + i
                m_idx = m_start + i
                
                ref_atoms.append(ref_residues[r_idx]['CA'])
                mobile_atoms.append(mob_residues[m_idx]['CA'])

        if not ref_atoms:
            print("No common CA atoms found for RMSD.")
            return float('inf')
            
        print(f"Aligned {len(ref_atoms)} residues for RMSD calculation.")

        super_imposer = Superimposer()
        super_imposer.set_atoms(ref_atoms, mobile_atoms)
        super_imposer.apply(mobile_structure.get_atoms())
        
        return super_imposer.rms

    def compare(self, ground_truth_path, original_path, refined_path, gt_chain=None):
        gt = self.load_structure(ground_truth_path, chain_id=gt_chain)
        orig = self.load_structure(original_path) # Original usually single chain AF model
        refined = self.load_structure(refined_path)
        
        rmsd_orig = self.calculate_rmsd(gt, orig)
        rmsd_refined = self.calculate_rmsd(gt, refined)
        
        return {
            "rmsd_original": rmsd_orig,
            "rmsd_refined": rmsd_refined,
            "improvement": rmsd_orig - rmsd_refined
        }
