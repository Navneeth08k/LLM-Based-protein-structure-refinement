class PromptBuilder:
    """
    Constructs prompts for the LLM to query biochemical priors for a specific protein region.
    """
    def __init__(self):
        pass

    def build_prompt(self, sequence, plddt, secondary_structure=None, context=None):
        """
        Creates a prompt describing the region.
        
        Args:
            sequence (str): Amino acid sequence of the region.
            plddt (list): List of pLDDT scores.
            secondary_structure (str, optional): Predicted secondary structure (e.g., from DSSP).
            context (str, optional): Description of the surrounding environment (e.g., "linker between two domains").
            
        Returns:
            str: The formatted prompt.
        """
        avg_plddt = sum(plddt)/len(plddt) if plddt else 0
        
        prompt = f"""
You are an expert structural biologist. I have a protein region that AlphaFold predicted with low confidence (pLDDT < 50), likely due to it being an Intrinsically Disordered Region (IDR) that folds upon binding.

**Biological Context:**
{context if context else "No specific context provided."}

**Region Details:**
- **Sequence:** {sequence}
- **Length:** {len(sequence)} residues
- **Average pLDDT:** {avg_plddt:.2f} (Low confidence)
"""
        if secondary_structure:
            prompt += f"- **Predicted Secondary Structure:** {secondary_structure}\n"

        prompt += """
**Task:**
Based *strictly* on the biological context above, predict the secondary structure this region adopts when bound.
**IMPORTANT:** Do NOT let the low pLDDT score dissuade you. The context confirms it folds.
If the context says it forms a helix, you MUST predict a helix and generate distance constraints for it.

**Output Format:**
Please provide your answer in JSON format with the following keys:
- "secondary_structure_prediction": "Helix" | "Sheet" | "Loop" | "Disordered"
- "confidence": "High" | "Medium" | "Low"
- "reasoning": "Brief explanation..."
- "constraints": [
    {"residue_index_1": int, "residue_index_2": int, "distance_angstroms": float, "type": "distance"}
]
**Important:** "residue_index_1" and "residue_index_2" should be the 1-based index within the *provided sequence snippet* (e.g., 1 is the first residue of the snippet).
"""
        return prompt
