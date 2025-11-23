import json
import numpy as np
from Bio.PDB import PDBParser
import os

class RegionFinder:
    """
    Identifies regions in a protein structure that require refinement based on
    AlphaFold confidence metrics (pLDDT).
    """
    def __init__(self, plddt_threshold=70.0, min_length=5):
        """
        Args:
            plddt_threshold (float): Residues with pLDDT below this are candidates.
            min_length (int): Minimum length of a contiguous low-confidence region to be flagged.
        """
        self.plddt_threshold = plddt_threshold
        self.min_length = min_length

    def find_regions_from_scores(self, plddt_scores):
        """
        Identifies contiguous regions with pLDDT < threshold.
        
        Args:
            plddt_scores (list or np.array): Array of pLDDT scores (0-100).
            
        Returns:
            list of tuples: [(start_idx, end_idx), ...] 0-indexed, exclusive end.
        """
        scores = np.array(plddt_scores)
        mask = scores < self.plddt_threshold
        
        # Find contiguous regions in the mask
        regions = []
        if not np.any(mask):
            return regions
            
        # Pad with False to detect edges
        padded_mask = np.concatenate(([False], mask, [False]))
        # Find where mask changes from False to True (start) and True to False (end)
        starts = np.where(padded_mask[:-1] != padded_mask[1:])[0][::2]
        ends = np.where(padded_mask[:-1] != padded_mask[1:])[0][1::2]
        
        for s, e in zip(starts, ends):
            if (e - s) >= self.min_length:
                regions.append((s, e))
                
        return regions

    def load_confidence_json(self, json_path):
        """Loads pLDDT scores from an AlphaFold JSON file."""
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # AlphaFold JSON structure usually has 'plddt' key
        if 'plddt' in data:
            return data['plddt']
        elif 'confidenceScore' in data:
            return data['confidenceScore']
        # Sometimes it might be nested or different format depending on version
        # Fallback or error handling could go here
        raise ValueError(f"Could not find 'plddt' or 'confidenceScore' key in {json_path}")

    def analyze(self, json_path):
        """
        Analyzes an AlphaFold prediction JSON to find regions for refinement.
        
        Args:
            json_path (str): Path to the confidence JSON file.
            
        Returns:
            dict: {
                'plddt_scores': [...],
                'regions': [(start, end), ...]
            }
        """
        scores = self.load_confidence_json(json_path)
        regions = self.find_regions_from_scores(scores)
        
        return {
            'plddt_scores': scores,
            'regions': regions
        }
